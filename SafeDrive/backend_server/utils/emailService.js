const nodemailer = require('nodemailer');

const transporter = nodemailer.createTransport({
    service: 'gmail',
    auth: {
        user: process.env.EMAIL_USER || 'safedrivereward@gmail.com', // Fallback for dev, but should be env in prod
        pass: process.env.EMAIL_PASS || 'zgbs gmhg kwvc vjde'
    }
});

const sendEmail = async (to, subject, text, html = null) => {
    try {
        const mailOptions = {
            from: '"SafeDrive Rewards" <safedrivereward@gmail.com>',
            to,
            subject,
            text,
            html: html || text // Use HTML if provided, fallback to text
        };

        const info = await transporter.sendMail(mailOptions);
        console.log('Email sent: ' + info.response);
        return true;
    } catch (error) {
        console.error('Error sending email:', error);
        return false;
    }
};

/**
 * Generates a professional HTML template for OTP emails.
 */
const generateOTPTemplate = (otp) => {
    return `
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta name="color-scheme" content="light dark">
        <meta name="supported-color-schemes" content="light dark">
        <title>SafeDrive Verification</title>
        <style>
            :root {
                color-scheme: light dark;
                supported-color-schemes: light dark;
            }
            @media (prefers-color-scheme: dark) {
                .body-bg { background-color: #0c111d !important; }
                .card-bg { background-color: #161b22 !important; border-color: #30363d !important; }
                .inner-card { background-color: #0d1117 !important; border-color: #21262d !important; }
                .text-main { color: #ffffff !important; }
                .text-sub { color: #8b949e !important; }
                .text-muted { color: #484f58 !important; }
                .logo-text { color: #ffffff !important; }
            }
        </style>
    </head>
    <body class="body-bg" style="margin: 0; padding: 0; background-color: #f8fafc; font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="table-layout: fixed;">
            <tr>
                <td align="center" style="padding: 40px 0;">
                    <!--[if mso]>
                    <table align="center" border="0" cellspacing="0" cellpadding="0" width="480">
                    <tr>
                    <td align="center" valign="top" width="480">
                    <![endif]-->
                    <table class="card-bg" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 480px; background-color: #ffffff; border-radius: 20px; overflow: hidden; border: 1px solid #e2e8f0; box-shadow: 0 10px 25px rgba(0,0,0,0.05);">
                        <!-- Accent Line -->
                        <tr>
                            <td style="height: 6px; background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%);"></td>
                        </tr>
                        <!-- Header -->
                        <tr>
                            <td align="center" style="padding: 40px 20px 20px 20px;">
                                <img src="https://swwwafedrive.vercel.app/logo.png" alt="SafeDrive" width="180" style="display: block; border: 0; margin-bottom: 0;">
                                <div class="logo-text" style="color: #0f172a; font-size: 24px; font-weight: 800; letter-spacing: 3px; text-transform: uppercase; margin-top: -30px;">SAFE DRIVE</div>
                                <div class="text-sub" style="color: #64748b; font-size: 11px; font-weight: 600; letter-spacing: 2px; text-transform: uppercase; margin-top: 4px;">Rewards Program</div>
                            </td>
                        </tr>
                        <!-- Content -->
                        <tr>
                            <td style="padding: 20px 40px 40px 40px; text-align: center;">
                                <div class="inner-card" style="background-color: #f1f5f9; border-radius: 16px; padding: 32px; border: 1px solid #e2e8f0;">
                                    <h2 class="text-main" style="color: #0f172a; font-size: 22px; font-weight: 700; margin: 0 0 12px 0;">Verify Your Identity</h2>
                                    <p class="text-sub" style="color: #64748b; font-size: 14px; line-height: 1.6; margin: 0 0 24px 0;">
                                        Use the security code below to complete your verification and access your rewards.
                                    </p>
                                    
                                    <div style="color: #3b82f6; font-size: 52px; font-weight: 800; letter-spacing: 12px; margin-bottom: 12px; font-family: 'Courier New', Courier, monospace;">
                                        ${otp}
                                    </div>
                                    <div class="text-muted" style="color: #94a3b8; font-size: 11px; text-transform: uppercase; font-weight: 700; letter-spacing: 2px;">
                                        Security Code
                                    </div>
                                </div>

                                <p class="text-muted" style="color: #94a3b8; font-size: 12px; margin: 32px 0 0 0;">
                                    This code is valid for <strong>10 minutes</strong>. <br>
                                    If you didn't request this code, please ignore this email.
                                </p>
                            </td>
                        </tr>
                        <!-- Footer -->
                        <tr>
                            <td class="inner-card" style="padding: 24px; border-top: 1px solid #e2e8f0; text-align: center; background-color: #f8fafc;">
                                <p class="text-muted" style="color: #94a3b8; font-size: 12px; margin: 0; line-height: 1.6;">
                                    &copy; 2026 SafeDrive Rewards. <br>
                                    Ensuring a safer mobility environment for everyone.
                                </p>
                            </td>
                        </tr>
                    </table>
                    <!--[if mso]>
                    </td>
                    </tr>
                    </table>
                    <![endif]-->
                </td>
            </tr>
        </table>
    </body>
    </html>
    `;
};

/**
 * Generates a template for Card Details.
 */
const generateCardDetailsTemplate = (name, cardNumber, cvv, expiry) => {
    return `
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta name="color-scheme" content="light dark">
        <meta name="supported-color-schemes" content="light dark">
        <title>Your SafeDrive Virtual Card</title>
        <style>
            :root {
                color-scheme: light dark;
                supported-color-schemes: light dark;
            }
            @media (prefers-color-scheme: dark) {
                .body-bg { background-color: #0c111d !important; }
                .card-bg { background-color: #161b22 !important; border-color: #30363d !important; }
                .inner-card { background-color: #0d1117 !important; border-color: #21262d !important; }
                .text-main { color: #ffffff !important; }
                .text-sub { color: #8b949e !important; }
                .text-muted { color: #484f58 !important; }
                .card-visual { background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important; border-color: #334155 !important; }
                .text-on-card { color: #f8fafc !important; }
            }
        </style>
    </head>
    <body class="body-bg" style="margin: 0; padding: 0; background-color: #f8fafc; font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="table-layout: fixed;">
            <tr>
                <td align="center" style="padding: 40px 0;">
                    <!--[if mso]>
                    <table align="center" border="0" cellspacing="0" cellpadding="0" width="480">
                    <tr>
                    <td align="center" valign="top" width="480">
                    <![endif]-->
                    <table class="card-bg" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 480px; background-color: #ffffff; border-radius: 20px; overflow: hidden; border: 1px solid #e2e8f0; box-shadow: 0 10px 25px rgba(0,0,0,0.05);">
                        <!-- Accent Line -->
                        <tr>
                            <td style="height: 6px; background: linear-gradient(90deg, #3b82f6 0%, #06b6d4 100%);"></td>
                        </tr>
                        <!-- Header -->
                        <tr>
                            <td align="center" style="padding: 40px 20px 20px 20px;">
                                <div style="color: #0f172a; font-size: 24px; font-weight: 800; letter-spacing: 1px; margin-bottom: 8px;" class="text-main">SafeDrive Rewards</div>
                                <div style="color: #64748b; font-size: 14px; font-weight: 500;" class="text-sub">Your Virtual Reward Card</div>
                            </td>
                        </tr>
                        <!-- Content -->
                        <tr>
                            <td style="padding: 0 40px 40px 40px;">
                                <div class="inner-card" style="background-color: #f8fafc; border-radius: 16px; padding: 24px; border: 1px solid #e2e8f0; margin-bottom: 24px;">
                                    <p class="text-sub" style="color: #475569; font-size: 14px; line-height: 1.6; margin: 0 0 20px 0; text-align: center;">
                                        Hello <strong>${name}</strong>,<br>
                                        Here are the details for your SafeDrive Virtual Card. Use this for toll payments and fuel rewards.
                                    </p>
                                    
                                    <!-- Virtual Card Visual -->
                                    <div class="card-visual" style="background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); border-radius: 12px; padding: 24px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); color: white; position: relative; overflow: hidden;">
                                        <!-- Chip -->
                                        <div style="width: 36px; height: 26px; background: #fbbf24; border-radius: 4px; margin-bottom: 20px; opacity: 0.9;"></div>
                                        
                                        <!-- Number -->
                                        <div style="font-family: 'Courier New', monospace; font-size: 20px; letter-spacing: 2px; margin-bottom: 20px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);" class="text-on-card">
                                            ${cardNumber.match(/.{1,4}/g).join(' ')}
                                        </div>
                                        
                                        <!-- Details -->
                                        <table width="100%" border="0" cellpadding="0" cellspacing="0">
                                            <tr>
                                                <td valign="bottom">
                                                    <div style="font-size: 10px; text-transform: uppercase; opacity: 0.8;" class="text-on-card">Card Holder</div>
                                                    <div style="font-size: 14px; font-weight: 600; text-transform: uppercase;" class="text-on-card">${name}</div>
                                                </td>
                                                <td align="right" valign="bottom">
                                                    <div style="font-size: 10px; text-transform: uppercase; opacity: 0.8;" class="text-on-card">Expires</div>
                                                    <div style="font-size: 14px; font-weight: 600;" class="text-on-card">${expiry}</div>
                                                </td>
                                            </tr>
                                        </table>
                                    </div>

                                    <div style="margin-top: 24px; text-align: center;">
                                        <p class="text-sub" style="color: #64748b; font-size: 12px; margin-bottom: 4px;">CVV Security Code</p>
                                        <div style="font-family: 'Courier New', monospace; font-size: 24px; font-weight: 700; color: #0f172a; letter-spacing: 4px;" class="text-main">${cvv}</div>
                                    </div>
                                </div>

                                <p class="text-muted" style="color: #94a3b8; font-size: 12px; text-align: center; margin: 0;">
                                    Keep these details secure. Do not share your CVV or OTP with anyone. SafeDrive will never ask for them.
                                </p>
                            </td>
                        </tr>
                        <!-- Footer -->
                        <tr>
                            <td class="inner-card" style="padding: 24px; border-top: 1px solid #e2e8f0; text-align: center; background-color: #f8fafc;">
                                <p class="text-muted" style="color: #94a3b8; font-size: 12px; margin: 0; line-height: 1.6;">
                                    &copy; 2026 SafeDrive Rewards. <br>
                                    <a href="#" style="color: #3b82f6; text-decoration: none;">Help Center</a> • <a href="#" style="color: #3b82f6; text-decoration: none;">Privacy Policy</a>
                                </p>
                            </td>
                        </tr>
                    </table>
                    <!--[if mso]>
                    </td>
                    </tr>
                    </table>
                    <![endif]-->
                </td>
            </tr>
        </table>
    </body>
    </html>
    `;
};

const getDefaultAvatar = (email) => {
    const crypto = require('crypto');
    const hash = crypto.createHash('md5').update(email.toLowerCase().trim()).digest('hex');
    return `https://www.gravatar.com/avatar/${hash}?d=identicon&s=200`;
};

module.exports = { sendEmail, generateOTPTemplate, generateCardDetailsTemplate, getDefaultAvatar };
