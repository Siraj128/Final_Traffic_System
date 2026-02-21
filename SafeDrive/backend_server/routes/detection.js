const express = require('express');
const router = express.Router();
const User = require('../models/User');

// Receive AI Detection Data
router.post('/upload', async (req, res) => {
    // Expected: { vehicle_number, violation_type, image_url, location }
    const { vehicle_number, violation_type } = req.body;

    try {
        // Find user by vehicle number
        const user = await User.findOne({ vehicle_number });

        if (user) {
            // Processing Logic
            if (violation_type === 'None') {
                // Good behavior -> Add Points
                user.rewards += 10;
                user.safe_streak += 1;
                // Cap compliance at 100
                user.compliance_score = Math.min(100, user.compliance_score + 1);
            } else {
                // Violation -> Deduct Points
                user.rewards = Math.max(0, user.rewards - 20);
                user.safe_streak = 0;
                user.compliance_score = Math.max(0, user.compliance_score - 5);

                user.violations.push({
                    type: violation_type,
                    penalty: 20,
                    date: Date.now()
                });
            }
            await user.save();
            res.json({ msg: 'Processed', user_updated: true });
        } else {
            res.json({ msg: 'Vehicle not registered', user_updated: false });
        }
    } catch (err) {
        console.error(err);
        res.status(500).send('Server Error');
    }
});

module.exports = router;
