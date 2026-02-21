
/**
 * otpService.js — Centralized OTP Management
 * 
 * Stores OTPs in-memory with expiration times.
 * Used for registration verification, RTO lookup, and virtual card access.
 */

const otpStore = new Map();

/**
 * Generate a 6-digit OTP and store it.
 * @param {string} email 
 * @param {number} ttlMinutes - Time to live in minutes (default 5)
 * @returns {string} - The generated OTP
 */
const generateOtp = (email, ttlMinutes = 5) => {
    const normalizedEmail = email.toLowerCase().trim();
    const otp = Math.floor(100000 + Math.random() * 900000).toString();
    otpStore.set(normalizedEmail, {
        code: otp,
        expires: Date.now() + ttlMinutes * 60 * 1000
    });
    console.log(`🔐 [OTP-SERVICE] Generated for ${normalizedEmail}: ${otp}`);
    return otp;
};

/**
 * Verify if the provided OTP is valid and not expired.
 * @param {string} email 
 * @param {string} otp 
 * @returns {boolean}
 */
const verifyOtp = (email, otp) => {
    const normalizedEmail = email.toLowerCase().trim();
    const record = otpStore.get(normalizedEmail);

    if (!record) {
        console.warn(`🔐 [OTP-SERVICE] No record found for ${normalizedEmail}`);
        return false;
    }

    if (Date.now() > record.expires) {
        otpStore.delete(normalizedEmail);
        console.warn(`🔐 [OTP-SERVICE] OTP expired for ${normalizedEmail}`);
        return false;
    }

    if (record.code === otp) {
        // Mark as verified but don't delete immediately so /register can check it
        record.verified = true;
        record.expires = Date.now() + 15 * 60 * 1000; // Extend to 15 mins for registration window
        console.log(`🔐 [OTP-SERVICE] Verified successfully for ${normalizedEmail}`);
        return true;
    }

    console.warn(`🔐 [OTP-SERVICE] Invalid OTP for ${normalizedEmail}. Expected ${record.code}, got ${otp}`);
    return false;
};

/**
 * Check if an email has been recently verified via OTP.
 * @param {string} email 
 * @returns {boolean}
 */
const isVerified = (email) => {
    const normalizedEmail = email ? email.toLowerCase().trim() : '';
    const record = otpStore.get(normalizedEmail);
    if (!record) {
        console.log(`🔐 [OTP-SERVICE] isVerified: No record for ${normalizedEmail}`);
        return false;
    }
    if (!record.verified) {
        console.log(`🔐 [OTP-SERVICE] isVerified: ${normalizedEmail} exists but not verified yet`);
        return false;
    }

    if (Date.now() > record.expires) {
        otpStore.delete(normalizedEmail);
        console.log(`🔐 [OTP-SERVICE] isVerified: ${normalizedEmail} verification expired`);
        return false;
    }

    console.log(`🔐 [OTP-SERVICE] isVerified: ${normalizedEmail} is VALID`);
    return true;
};

/**
 * Clear any existing OTP for an email.
 * @param {string} email 
 */
const clearOtp = (email) => {
    const normalizedEmail = email.toLowerCase().trim();
    otpStore.delete(normalizedEmail);
};

module.exports = {
    generateOtp,
    verifyOtp,
    isVerified,
    clearOtp
};
