const mongoose = require('mongoose');
const User = require('./models/User');

mongoose.connect('mongodb://localhost:27017/safedrive_rewards', {
    useNewUrlParser: true,
    useUnifiedTopology: true
}).then(async () => {
    console.log('Connected to DB');
    const users = await User.find({}, 'name email vehicle_number card_number');
    console.log('Users found:', users.length);
    users.forEach(u => {
        console.log(`Name: ${u.name}, Email: ${u.email}, Plate: '${u.vehicle_number}', Card: ${u.card_number}`);
    });
    process.exit();
}).catch(err => {
    console.error(err);
    process.exit(1);
});
