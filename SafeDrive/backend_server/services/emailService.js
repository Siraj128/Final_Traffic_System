const nodemailer = require('nodemailer');
require('dotenv').config();

// Initialize Transporter
const transporter = nodemailer.createTransport({
    service: 'gmail',
    auth: {
        user: process.env.EMAIL_USER,
        pass: process.env.EMAIL_PASS
    }
});

/**
 * Send a generic email
 * @param {string} to - Recipient Email
 * @param {string} subject - Email Subject
 * @param {string} text - Plain text body
 * @param {string} html - HTML body
 */
const sendEmail = async (to, subject, text, html) => {
    try {
        if (!process.env.EMAIL_USER || !process.env.EMAIL_PASS) {
            console.warn("⚠️ Email credentials missing. Check .env");
            return { success: false, message: "Server email not configured" };
        }

        const info = await transporter.sendMail({
            from: `"SafeDrive Rewards" <${process.env.EMAIL_USER}>`,
            to,
            subject,
            text,
            html
        });
        console.log(`📧 Email sent to ${to}: ${info.messageId}`);
        return { success: true, messageId: info.messageId };
    } catch (error) {
        console.error("❌ Email Send Error:", error);
        return { success: false, error: error.message };
    }
};

/**
 * Send OTP for Vehicle Verification
 * @param {string} email 
 * @param {string} otp 
 * @param {string} plateNumber 
 */
const sendRtoOtp = async (email, otp, plateNumber) => {
    if (!email) return { success: false, error: "No email provided" };

    const subject = "SafeDrive - Vehicle Verification Code";
    const text = `Your verification code for Vehicle ${plateNumber || 'Registration'} is: ${otp}. Valid for 5 minutes.`;
    const html = `
        <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #ddd; max-width: 500px;">
            <h2 style="color: #6C63FF;">SafeDrive Vehicle Verification</h2>
            <p>You are verifying ownership of vehicle <b>${plateNumber || 'Registration'}</b>.</p>
            <p>Your Verification Code is:</p>
            <h1 style="background: #f4f4f4; padding: 10px; text-align: center; letter-spacing: 5px;">${otp}</h1>
            <p>This code expires in 5 minutes.</p>
            <hr>
            <small>If you didn't request this, please ignore this email.</small>
        </div>
    `;

    return await sendEmail(email, subject, text, html);
};

/**
 * Send Virtual Card Details
 * @param {string} email 
 * @param {object} cardData 
 */
const sendCardDetails = async (email, cardData) => {
    const subject = "SafeDrive - Your Virtual Card Details";
    const text = `Here are your Virtual Card details: Number: ${cardData.cardNumber}, CVV: ${cardData.cvv}, Expiry: ${cardData.expiry}. Keep this safe!`;
    const html = `
        <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #ddd; max-width: 500px; background: #1e1e2e; color: white; border-radius: 15px;">
            <h2 style="color: #4CAF50;">SafeDrive Virtual Card</h2>
            <p>Access your rewards anywhere.</p>
            
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 12px; margin: 20px 0;">
                <p style="font-size: 18px; letter-spacing: 2px; margin-bottom: 20px; font-family: monospace;">${cardData.cardNumber}</p>
                <div style="display: flex; justify-content: space-between;">
                    <span>Expiry: <b>${cardData.expiry}</b></span>
                    <span>CVV: <b>${cardData.cvv}</b></span>
                </div>
                <p style="margin-top: 20px; text-transform: uppercase;">${cardData.ownerName}</p>
            </div>
            
            <p style="color: #aaa; font-size: 12px;">⚠️ Do not share this email with anyone.</p>
        </div>
    `;

    return await sendEmail(email, subject, text, html);
};

module.exports = {
    sendEmail,
    sendRtoOtp,
    sendCardDetails
};
