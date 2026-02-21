
require('dotenv').config();
const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');

const db = require('./db');

// Routes
const authRoutes = require('./routes/auth');
// Disabled until refactored:
// const userRoutes = require('./routes/user');
const rewardRoutes = require('./routes/rewards');
// const detectionRoutes = require('./routes/detection');

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(bodyParser.json());

// Request Logger
// Request Logger
app.use((req, res, next) => {
    console.log(`[REQUEST] ${req.method} ${req.originalUrl} from ${req.ip}`);

    // Log response status
    const originalSend = res.send;
    res.send = function (body) {
        console.log(`[RESPONSE] ${res.statusCode} ${req.originalUrl}`);
        return originalSend.call(this, body);
    };
    next();
});

// Database Connection Check
db.query('SELECT NOW()', (err, res) => {
    if (err) {
        console.error('❌ Postgres Connection Error', err);
    } else {
        console.log('✅ Postgres Connected:', res.rows[0].now);
    }
});

// Routes Middleware
app.use('/api/auth', authRoutes);
app.use('/api/auth/rto', require('./routes/rto_auth')); // [NEW] RTO Lookup
app.use('/api/vehicles', require('./routes/vehicles')); // [NEW] Postgres
app.use('/api/wallet', require('./routes/wallet'));     // [Rewritten] Postgres
app.use('/api/notifications', require('./routes/notifications')); // [Re-enabled] Mock
app.use('/api/analytics', require('./routes/analytics')); // [Rewritten] Mock
app.use('/api/leaderboard', require('./routes/leaderboard')); // [Rewritten] Postgres
// app.use('/api/user', userRoutes);
app.use('/api/rewards', rewardRoutes);
// app.use('/api/detection', detectionRoutes);
app.use('/api/card', require('./routes/card'));

// Test Route
app.get('/', (req, res) => {
    res.send('SafeDrive Rewards Backend Running 🚀 (Postgres)');
});

// Start Server
app.listen(PORT, () => {
    console.log(`🚀 Server running on port ${PORT}`);
});
