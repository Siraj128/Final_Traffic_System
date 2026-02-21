const express = require('express');
const router = express.Router();
const db = require('../db');
const auth = require('../middleware/auth');

// @route   GET /api/wallet/my
// @desc    Get wallet balance
// @access  Private
router.get('/my', auth, async (req, res) => {
    try {
        const query = 'SELECT wallet_balance, total_earned_points FROM users WHERE user_id = $1';
        const result = await db.query(query, [req.user.id]);

        if (result.rows.length === 0) return res.status(404).json({ msg: 'User not found' });

        const user = result.rows[0];
        res.json({
            success: true,
            balance: parseFloat(user.wallet_balance || 0.00),
            wallet_balance: parseFloat(user.wallet_balance || 0.00),
            points: parseInt(user.total_earned_points || 0),
            wallet_points: parseInt(user.total_earned_points || 0)
        });
    } catch (err) {
        console.error(err.message);
        res.status(500).send('Server Error');
    }
});

// @route   GET /api/wallet/history
// @desc    Get transactions
// @access  Private
router.get('/history', auth, async (req, res) => {
    try {
        const query = 'SELECT * FROM transactions WHERE user_id = $1 ORDER BY created_at DESC LIMIT 50';
        const result = await db.query(query, [req.user.id]);

        // App expects List directly
        res.json(result.rows);
    } catch (err) {
        console.error(err.message);
        res.status(500).send('Server Error');
    }
});

module.exports = router;
