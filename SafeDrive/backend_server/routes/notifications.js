const express = require('express');
const router = express.Router();

// Get Notifications
router.get('/:plateNumber', async (req, res) => {
    try {
        // Mock Notifications
        // Real implementation would query a Notification model

        const notifications = [
            {
                id: '1',
                title: 'Reward Earned',
                message: 'You earned 50 points for safe driving today!',
                timestamp: new Date().toISOString(),
                type: 'REWARD',
                isRead: false
            },
            {
                id: '2',
                title: 'Toll Deducted',
                message: '₹50 deducted at Electronic City Toll Plaza.',
                timestamp: new Date(Date.now() - 86400000).toISOString(), // Yesterday
                type: 'TOLL',
                isRead: true
            },
            {
                id: '3',
                title: 'Weekly Summary',
                message: 'You drove 120km this week with 98% compliance.',
                timestamp: new Date(Date.now() - 172800000).toISOString(), // 2 days ago
                type: 'INFO',
                isRead: true
            }
        ];

        res.json(notifications);
    } catch (err) {
        res.status(500).json({ msg: 'Server Error' });
    }
});

module.exports = router;
