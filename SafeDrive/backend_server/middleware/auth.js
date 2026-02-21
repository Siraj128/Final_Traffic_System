const jwt = require('jsonwebtoken');

module.exports = function (req, res, next) {
    // Get token from header
    const token = req.header('Authorization')?.replace('Bearer ', '');

    // Check if not token
    if (!token) {
        console.log('[AUTH-ERROR] No Token Provided');
        return res.status(401).json({ msg: 'No token, authorization denied' });
    }

    // Verify token
    try {
        const decoded = jwt.verify(token, process.env.JWT_SECRET || 'secret_token');
        req.user = decoded.user;
        // console.log(`[AUTH-SUCCESS] User: ${req.user.id}`); // Too verbose?
        next();
    } catch (err) {
        console.log('[AUTH-ERROR] Invalid Token:', err.message);
        res.status(401).json({ msg: 'Token is not valid' });
    }
};
