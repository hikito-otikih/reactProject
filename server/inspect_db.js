import sqlite3 from 'sqlite3';

const db = new sqlite3.Database('./static_db/places.db', (err) => {
    if (err) {
        console.error('Error opening DB:', err);
        process.exit(1);
    }
    console.log('✓ DB opened\n');
});

// Get all tables
db.all("SELECT name FROM sqlite_master WHERE type='table'", (err, tables) => {
    if (err) {
        console.error('Error getting tables:', err);
        db.close();
        return;
    }
    console.log('Tables:', tables.map(t => t.name));

    if (tables.length > 0) {
        const tableName = tables[0].name;
        console.log(`\nAnalyzing table: ${tableName}`);

        // Get columns
        db.all(`PRAGMA table_info(${tableName})`, (err, cols) => {
            if (err) {
                console.error('Error getting columns:', err);
                return;
            }
            console.log('Columns:', cols.map(c => `${c.name} (${c.type})`).join(', '));

            // Get row count
            db.get(`SELECT COUNT(*) as count FROM ${tableName}`, (err, result) => {
                if (err) {
                    console.error('Error getting count:', err);
                    return;
                }
                console.log(`Total rows: ${result.count}`);

                // Sample data
                db.all(`SELECT * FROM ${tableName} LIMIT 5`, (err, rows) => {
                    if (err) {
                        console.error('Error getting sample data:', err);
                    } else {
                        console.log('\nSample data:');
                        console.log(JSON.stringify(rows, null, 2));
                    }
                    db.close();
                });
            });
        });
    } else {
        db.close();
    }
});
