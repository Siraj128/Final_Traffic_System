const mongoose = require('mongoose');
const User = require('./models/User');

mongoose.connect('mongodb://localhost:27017/safedrive_rewards', {
    useNewUrlParser: true,
    useUnifiedTopology: true
}).then(async () => {
    console.log('Connected to DB');
    const users = await User.find({ card_number: { $exists: false } }); // Find users without card
    console.log(`Found ${users.length} users without card details.`);

    for (const user of users) {
        user.card_number = '4' + Math.floor(Math.random() * 1000000000000000).toString().padStart(15, '0');
        user.card_cvv = Math.floor(Math.random() * 900 + 100).toString();
        user.card_expiry = '12/30';
        await user.save();
        console.log(`Updated user: ${user.email} with Card: ${user.card_number}`);
    }

    // Double check all users
    const allUsers = await User.find({});
    allUsers.forEach(u => {
        if (!u.card_number) {
            console.log(`Still missing for: ${u.email}`);
        } else {
            console.log(`Verified card for: ${u.email} -> ${u.card_number}`);
        }
    });

    process.exit();
}).catch(err => {
    console.error(err);
    process.exit(1);
});
