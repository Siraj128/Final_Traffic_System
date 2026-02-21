const express = require('express');
const router = express.Router();

// Get Analytics
router.get('/:plateNumber', async (req, res) => {
    try {
        const { plateNumber } = req.params;

        // Mock Analytics Data for Demo - Mapping to Flutter expected keys
        const analyticsData = {
            compliance_score: 88.0, // App expects this
            avg_speed: 45,
            safety_score: 92,
            riskLevel: 'SAFE',
            safeStreakDays: 7,
            totalViolations: 0,
            trips: [{}, {}, {}], // Mock trips for list length
            insights: [
                "Great job! No speeding violations this week.",
                "Try to maintain consistent speed for better fuel efficiency.",
                "Your compliance score is in the top 10%!"
            ]
        };

        res.json(analyticsData);
    } catch (err) {
        res.status(500).json({ msg: 'Server Error' });
    }
});

module.exports = router;
