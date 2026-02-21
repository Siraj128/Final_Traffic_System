const mongoose = require('mongoose');

const UserSchema = new mongoose.Schema({
    name: { type: String, required: true },
    email: { type: String, required: true, unique: true },
    password: { type: String }, // Optional for Google Users
    vehicle_number: { type: String }, // Optional initially
    mobile: { type: String },
    avatar: { type: String }, // URL to profile pic or Gravatar
    otp: { type: String },
    otpExpires: { type: Date },
    // Virtual Card Details
    card_number: { type: String, unique: true, sparse: true },
    card_cvv: { type: String },
    card_expiry: { type: String },
    card_pin: { type: String },
    googleId: { type: String, unique: true, sparse: true },
    city: { type: String },
    fastag_id: { type: String },
    is_profile_complete: { type: Boolean, default: false },
    created_at: { type: Date, default: Date.now },
    last_login: { type: Date },
    vehicle_type: { type: String, default: 'Car' },
    tier: { type: String, default: 'Bronze' }, // Bronze, Silver, Gold
    rewards: { type: Number, default: 0 },
    compliance_score: { type: Number, default: 100 },
    safe_streak: { type: Number, default: 0 },
    violations: [
        {
            type: { type: String },
            date: { type: Date, default: Date.now },
            penalty: { type: Number }
        }
    ],
    transaction_history: [
        {
            type: { type: String }, // 'Earned', 'Redeemed', 'Toll Paid'
            amount: { type: Number },
            date: { type: Date, default: Date.now }
        }
    ]
});

module.exports = mongoose.model('User', UserSchema);
