import sqlite3 from 'sqlite3';

const db = new sqlite3.Database('./static_db/places.db', sqlite3.OPEN_READONLY, (err) => {
    if (err) {
        console.error('Error:', err);
        process.exit(1);
    }

    // Simulate the query with list_id as array
    const ids = [1, 2, 3, 4, 5];
    const placeholders = ids.map(() => '?').join(',');
    const sql = `SELECT * FROM places WHERE rowid IN (${placeholders})`;

    console.log('Query:', sql);
    console.log('Params:', ids);
    console.log('');

    db.all(sql, ids, (err, rows) => {
        if (err) {
            console.error('Error:', err);
        } else {
            console.log(`Found ${rows.length} rows:\n`);
            rows.forEach((row, i) => {
                console.log(`Row ${i + 1}: ${row.title}`);
                console.log(`  Address: ${row.address}`);
                console.log(`  Rating: ${row.rating}`);
                console.log(`  Phone: ${row.phone}\n`);
            });
        }
        db.close();
    });
});
