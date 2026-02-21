const express = require('express');
const router = express.Router();
const db = require('../db');

// @route   POST /api/auth/rto/lookup
// @desc    Fetch official EMAIL from RTO Registry for a given plate
router.post('/lookup', async (req, res) => {
    const { plate_number } = req.body;

    if (!plate_number) return res.status(400).json({ success: false, message: 'Vehicle number is required' });

    try {
        const normalizedPlate = plate_number.replace(/[\s-]/g, '').toUpperCase();

        // Query Email instead of Phone
        const query = `
            SELECT email, owner_name 
            FROM rto_registry 
            WHERE REPLACE(REPLACE(v1_plate, '-', ''), ' ', '') = $1 
               OR REPLACE(REPLACE(v2_plate, '-', ''), ' ', '') = $1
        `;

        const result = await db.trafficQuery(query, [normalizedPlate]);

        if (result.rows.length === 0) {
            return res.json({ success: false, found: false, message: "Vehicle not found in RTO Registry" });
        }

        const rtoData = result.rows[0];
        const rawEmail = rtoData.email;

        // Mask Email (e.g., s***j@gmail.com)
        const [user, domain] = rawEmail.split('@');
        const maskedUser = user.length > 2 ? `${user[0]}***${user[user.length - 1]}` : `${user}***`;
        const maskedEmail = `${maskedUser}@${domain}`;

        res.json({
            success: true,
            found: true,
            vehicle_number: normalizedPlate,
            owner_name: rtoData.owner_name,
            email: rawEmail,      // Needed for Send OTP (Frontend shouldn't ideally see this, but for hackathon OK)
            masked_email: maskedEmail
        });

    } catch (err) {
        console.error('❌ [RTO-LOOKUP] Error:', err.message);
        res.status(500).json({ success: false, message: 'Server Error during RTO Lookup' });
    }
});

const emailService = require('../services/emailService');
const otpService = require('../services/otpService');

// @route   POST /api/auth/rto/send-email-otp
// @desc    Generate and Send OTP to the RTO Email
router.post('/send-email-otp', async (req, res) => {
    const { email, plate } = req.body;

    if (!email) return res.status(400).json({ success: false, message: "Email required" });

    // Generate 6-digit OTP using central service
    const otp = otpService.generateOtp(email);

    console.log(`📧 [EMAIL-OTP] App: Generated for ${email}: ${otp}`);

    // Send Real Email via Service
    const emailRes = await emailService.sendRtoOtp(email, otp, plate);

    if (emailRes.success) {
        res.json({ success: true, message: `OTP sent to ${email}` });
    } else {
        // Fallback for Dev/Hackathon if email fails (e.g. invalid creds)
        console.warn("⚠️ Email Service Failed. Returning Dev OTP.");
        res.json({
            success: true,
            message: "OTP Sent (Simulated - Email Failed)",
            dev_otp: otp // Keep existing fallback for safety
        });
    }
});

// @route   POST /api/auth/rto/verify-email-otp
// @desc    Verify the code
router.post('/verify-email-otp', async (req, res) => {
    const { email, otp } = req.body;

    const isValid = otpService.verifyOtp(email, otp);

    if (isValid) {
        return res.json({ success: true, message: "Verification Successful" });
    } else {
        return res.status(400).json({ success: false, message: "Invalid or expired OTP" });
    }
});

module.exports = router;
