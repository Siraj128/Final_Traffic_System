
const express = require('express');
const router = express.Router();
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const db = require('../db');
const emailService = require('../services/emailService');
const otpService = require('../services/otpService');

// --- HELPER: Generate Default Avatar ---
const getDefaultAvatar = (email) => {
    return `https://ui-avatars.com/api/?name=${encodeURIComponent(email)}&background=random`;
};

// --- 1. CHECK VEHICLE (GET /api/auth/check-vehicle/:plate) ---
router.get('/check-vehicle/:plate', async (req, res) => {
    const plate = req.params.plate.toUpperCase().replace(/[\s-]/g, '');
    try {
        // Query Neon RTO Registry
        const query = `
            SELECT phone_number, owner_name 
            FROM rto_registry 
            WHERE REPLACE(REPLACE(v1_plate, '-', ''), ' ', '') = $1 
               OR REPLACE(REPLACE(v2_plate, '-', ''), ' ', '') = $1
        `;
        const result = await db.trafficQuery(query, [plate]);

        if (result.rows.length > 0) {
            const { phone_number, owner_name } = result.rows[0];
            // Mask Phone for Security
            const maskedPhone = phone_number.replace(/.(?=.{4})/g, '*');
            res.json({
                success: true,
                found: true,
                owner: owner_name,
                phone: maskedPhone,
                message: `OTP sent to ${maskedPhone}`
            });
        } else {
            res.json({ success: true, found: false, message: "Vehicle not found in official registry. Proceeding with standard signup." });
        }
    } catch (err) {
        console.error(err);
        res.status(500).json({ msg: "Registration check failed" });
    }
});

// --- 2. SEND OTP (POST /api/auth/send-otp) ---
router.post('/send-otp', async (req, res) => {
    const { email, plate } = req.body;
    if (!email) return res.status(400).json({ msg: "Email is required" });

    try {
        const otp = otpService.generateOtp(email);
        const emailRes = await emailService.sendRtoOtp(email, otp, plate || 'Verification');

        if (emailRes.success) {
            res.json({ success: true, message: "OTP sent successfully" });
        } else {
            console.warn("⚠️ Email failed, providing dev otp (Hackathon Fallback)");
            res.json({ success: true, message: "OTP Sent (Simulated)", dev_otp: otp });
        }
    } catch (err) {
        console.error(err);
        res.status(500).json({ msg: "Failed to send OTP" });
    }
});

// --- 3. VERIFY OTP (POST /api/auth/verify-otp) ---
router.post('/verify-otp', async (req, res) => {
    const { email, otp } = req.body;
    if (!email || !otp) return res.status(400).json({ msg: "Email and OTP are required" });

    const isValid = otpService.verifyOtp(email, otp);
    if (isValid) {
        res.json({ success: true, message: "OTP Verified" });
    } else {
        res.status(400).json({ success: false, message: "Invalid or expired OTP" });
    }
});

// --- 3. REGISTER (POST /api/auth/register) ---
router.post('/register', async (req, res) => {
    // Destructure with possible aliases from App
    const { name, owner_name, email, password, vehicle_number, plate_number, mobile, vehicle_type, otp_verified } = req.body;

    const userName = name || owner_name;
    const vehicleNumber = vehicle_number || plate_number;

    if (!userName || !email || !password || !mobile || !vehicleNumber || !vehicle_type) {
        console.log("❌ Missing Fields:", req.body);
        return res.status(400).json({ msg: 'Please provide all required fields' });
    }

    // [RULE] Normalize Vehicle Number (Remove spaces and dashes)
    const normalizedPlate = vehicleNumber ? vehicleNumber.toUpperCase().replace(/[\s-]/g, '') : null;

    try {
        // --- 0. OTP ENFORCEMENT ---
        // Verify via backend service or client flag (backend service is more secure)
        const isVerifiedBackend = otpService.isVerified(email);
        console.log(`🛡️ [REGISTER] Attempt for: ${email}, Plate: ${normalizedPlate}`);
        console.log(`🛡️ [REGISTER] Client Verified: ${otp_verified}, Backend Verified: ${isVerifiedBackend}`);

        if (normalizedPlate && !otp_verified && !isVerifiedBackend) {
            console.warn(`🛑 [REGISTER] Blocked: Verification missing for ${email}`);
            return res.status(400).json({ success: false, msg: "Please verify your vehicle ownership via OTP first." });
        }

        // 1. Check if user exists
        const userCheck = await db.query('SELECT * FROM users WHERE email = $1', [email]);
        if (userCheck.rows.length > 0) {
            return res.status(400).json({ msg: 'User already exists' });
        }

        // 2. Hash Password
        const salt = await bcrypt.genSalt(10);
        const hashedPassword = await bcrypt.hash(password, salt);

        // 3. --- REWARD CLAIM & DATA MERGE LOGIC (Enhanced for Multi-Vehicle) ---
        let initial_points = 0;
        let initial_wallet = 0.00;
        let rtoProfile = null;

        try {
            // A. Fetch RTO Registry Profile by Phone
            const rtoQuery = 'SELECT * FROM rto_registry WHERE phone_number = $1';
            const rtoRes = await db.trafficQuery(rtoQuery, [mobile]);
            if (rtoRes.rows.length > 0) {
                rtoProfile = rtoRes.rows[0];
                console.log(`✅ [AUTH] Linked RTO Profile for ${mobile}: ${rtoProfile.owner_name}`);
            }

            // B. Check Traffic DB for "Ghost Points" (Multi-Slot sum)
            const ghostQuery = 'SELECT * FROM user_rewards WHERE phone_number = $1';
            const ghostRes = await db.trafficQuery(ghostQuery, [mobile]);

            if (ghostRes.rows.length > 0) {
                const row = ghostRes.rows[0];
                const earned = row.total_points || ((row.v1_points || 0) + (row.v2_points || 0));

                if (earned > 0) {
                    initial_points = earned;
                    initial_wallet = (earned / 100) * 0.50;
                    console.log(`🎁 [AUTH] CLAIMED TOTAL: ${earned} points (V1+V2) for Phone: ${mobile}`);

                    // Clear Ghost Record
                    await db.trafficQuery('DELETE FROM user_rewards WHERE phone_number = $1', [mobile]);
                }
            }
        } catch (err) {
            console.warn("⚠️ RTO/Ghost Sync Failed:", err.message);
        }

        // 4. Insert New User
        const insertUserQuery = `
            INSERT INTO users (name, full_name, email, password_hash, mobile, avatar_url, total_earned_points, wallet_balance, created_at)
            VALUES ($1, $1, $2, $3, $4, $5, $6, $7, NOW())
            RETURNING user_id, name, email, role, total_earned_points, total_earned_points AS wallet_points, wallet_balance, wallet_balance AS balance
        `;
        const avatar = req.body.avatar || getDefaultAvatar(email);
        const newUserRes = await db.query(insertUserQuery, [
            userName, email, hashedPassword, mobile, avatar, initial_points, initial_wallet
        ]);
        const user = newUserRes.rows[0];

        // 5. Insert Multi-Vehicles from RTO (Strict Sync)
        if (rtoProfile) {
            // Insert Vehicle 1
            if (rtoProfile.v1_plate) {
                const q = `INSERT INTO vehicles (user_id, plate_number, vehicle_type, is_primary, rto_slot) 
                           VALUES ($1, $2, $3, TRUE, 1) 
                           ON CONFLICT (plate_number) DO UPDATE SET user_id = $1, is_primary = TRUE, rto_slot = 1, vehicle_type = $3`;
                await db.query(q, [user.user_id, rtoProfile.v1_plate, rtoProfile.v1_type || 'Car']);
                console.log(`🚗 [AUTH] Auto-Imported V1: ${rtoProfile.v1_plate} (${rtoProfile.v1_type})`);
            }
            // Insert Vehicle 2
            if (rtoProfile.v2_plate) {
                const q = `INSERT INTO vehicles (user_id, plate_number, vehicle_type, is_primary, rto_slot) 
                           VALUES ($1, $2, $3, FALSE, 2) 
                           ON CONFLICT (plate_number) DO UPDATE SET user_id = $1, rto_slot = 2, vehicle_type = $3`;
                await db.query(q, [user.user_id, rtoProfile.v2_plate, rtoProfile.v2_type || 'Car']);
                console.log(`🚗 [AUTH] Auto-Imported V2: ${rtoProfile.v2_plate} (${rtoProfile.v2_type})`);
            }
        } else if (normalizedPlate) {
            // Fallback: If not in RTO (rare), insert as Car.
            // But checking RTO for the *Input Plate* specifically to catch edge cases
            // where phone might not have matched but plate exists in RTO.
            const rtoCheck = await db.trafficQuery("SELECT * FROM rto_registry WHERE v1_plate = $1 OR v2_plate = $1", [normalizedPlate]);
            if (rtoCheck.rows.length > 0) {
                // Found deeper link via plate
                const deepProfile = rtoCheck.rows[0];
                // Recursive call or just duplicate logic? Let's just update the user with this profile next time.
                // For now, insert as single, but warn.
                console.log(`⚠️ [AUTH] Plate ${normalizedPlate} found in RTO but phone didn't match. Partial sync.`);
            }

            const q = `INSERT INTO vehicles (user_id, plate_number, vehicle_type, is_primary, rto_slot) 
                       VALUES ($1, $2, $3, TRUE, 1) ON CONFLICT (plate_number) DO UPDATE SET user_id = $1`;
            await db.query(q, [user.user_id, normalizedPlate, vehicle_type || 'Car']);
        }

        // 6. Return Token & User
        const payload = { user: { id: user.user_id } };
        jwt.sign(payload, process.env.JWT_SECRET || 'secret_token', { expiresIn: 360000 }, (err, token) => {
            if (err) throw err;
            res.json({
                token,
                user,
                message: initial_points > 0 ? `Welcome! ${initial_points} points claimed from your car.` : "Welcome to SafeDrive!"
            });
        });

    } catch (err) {
        console.error(err.message);
        res.status(500).send('Server Error');
    }
});

// --- LOGIN (POST /api/auth/login) ---
router.post('/login', async (req, res) => {
    // Destructure aliases
    const { email, password, vehicle_number, identifier } = req.body;

    // Resolve login identifier
    // App sends 'identifier', which could be email OR plate
    const loginValue = identifier || email || vehicle_number;

    if (!loginValue || !password) {
        return res.status(400).json({ msg: 'Please provide email/vehicle and password' });
    }

    try {
        let user;
        const isEmail = loginValue.includes('@');

        if (!isEmail) {
            // Assume Vehicle Number -> Find User
            // Normalize the plate input (remove spaces/dashes)
            const plateSearch = loginValue.toUpperCase().replace(/[\s-]/g, '');
            const vehRes = await db.query('SELECT user_id FROM vehicles WHERE plate_number = $1', [plateSearch]);
            if (vehRes.rows.length === 0) return res.status(400).json({ msg: 'Vehicle not found or not registered' });

            const userId = vehRes.rows[0].user_id;
            // Fetch User
            const userRes = await db.query('SELECT * FROM users WHERE user_id = $1', [userId]);
            if (userRes.rows.length === 0) return res.status(400).json({ msg: 'User not found for this vehicle' });
            user = userRes.rows[0];
        } else {
            // Fetch by Email
            const userRes = await db.query('SELECT * FROM users WHERE email = $1', [loginValue]);
            user = userRes.rows[0];
        }

        if (!user) return res.status(400).json({ msg: 'Invalid Credentials' });

        // Check Password
        const isMatch = await bcrypt.compare(password, user.password_hash);
        if (!isMatch) return res.status(400).json({ msg: 'Invalid Credentials' });

        // Update Last Login
        await db.query('UPDATE users SET last_login = NOW() WHERE user_id = $1', [user.user_id]);

        // Return Token
        const payload = { user: { id: user.user_id } };
        jwt.sign(payload, process.env.JWT_SECRET || 'secret_token', { expiresIn: 360000 }, (err, token) => {
            if (err) throw err;
            res.json({ token, user });
        });

    } catch (err) {
        console.error(err.message);
        res.status(500).send('Server Error');
    }
});

// --- GOOGLE LOGIN (POST /api/auth/google) ---
router.post('/google', async (req, res) => {
    const { email, name, picture, googleId } = req.body;

    try {
        // 1. Check if user exists
        const userRes = await db.query('SELECT * FROM users WHERE email = $1', [email]);

        if (userRes.rows.length > 0) {
            // User Exists -> Login
            const user = userRes.rows[0];

            // Update Google ID/Avatar if missing
            if (!user.google_id || !user.avatar_url) {
                await db.query('UPDATE users SET google_id = $1, avatar_url = COALESCE(avatar_url, $2) WHERE user_id = $3',
                    [googleId, picture, user.user_id]);
            }

            const payload = { user: { id: user.user_id } };
            jwt.sign(payload, process.env.JWT_SECRET || 'secret_token', { expiresIn: 360000 }, (err, token) => {
                if (err) throw err;
                res.json({ token, user, isNewUser: false });
            });
        } else {
            // User Not Found -> Return isNewUser flag
            res.json({
                isNewUser: true,
                email,
                name,
                picture,
                googleId
            });
        }
    } catch (err) {
        console.error("Google Auth Error:", err.message);
        res.status(500).send('Server Error');
    }
});

// --- GOOGLE REGISTER (POST /api/auth/google/register) ---
router.post('/google/register', async (req, res) => {
    const { name, email, googleId, avatar, vehicle_number, vehicle_type, mobile } = req.body;

    try {
        // 1. Create User
        // Check if exists again just in case
        const check = await db.query('SELECT * FROM users WHERE email = $1', [email]);
        if (check.rows.length > 0) return res.status(400).json({ msg: "User already registered" });

        // Insert User
        const insertUserQuery = `
            INSERT INTO users (name, full_name, email, google_id, avatar_url, mobile, total_earned_points, wallet_balance, created_at)
            VALUES ($1, $1, $2, $3, $4, $5, 0, 0.00, NOW())
            RETURNING user_id, name, email, role, total_earned_points, wallet_balance
        `;
        const newUserRes = await db.query(insertUserQuery, [name, email, googleId, avatar, mobile]);
        const user = newUserRes.rows[0];

        // 2. Add Vehicle
        if (vehicle_number) {
            const cleanPlate = vehicle_number.toUpperCase().replace(/[\s-]/g, '');
            const vQuery = `
                INSERT INTO vehicles (user_id, plate_number, vehicle_type, is_primary)
                VALUES ($1, $2, $3, TRUE)
                ON CONFLICT (plate_number) DO UPDATE SET user_id = $1
            `;
            await db.query(vQuery, [user.user_id, cleanPlate, vehicle_type || 'Car']);
        }

        // 3. Generate Token
        const payload = { user: { id: user.user_id } };
        jwt.sign(payload, process.env.JWT_SECRET || 'secret_token', { expiresIn: 360000 }, (err, token) => {
            if (err) throw err;
            res.json({ token, user });
        });

    } catch (err) {
        console.error("Google Register Error:", err.message);
        res.status(500).send('Server Error');
    }
});

module.exports = router;
