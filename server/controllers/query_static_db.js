// path : /static_db/places.db
import path from "path";
import { fileURLToPath } from "url";
import sqlite3 from "sqlite3";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const DB_PATH = path.join(__dirname, "..", "static_db", "places.db");

export const queryStaticDB = async (req, res) => {
    try {
        const { list_id, list_id_of_places } = req.body || {};

        // Normalize input: accept either single list_id or array of ids
        let ids = [];
        if (Array.isArray(list_id)) {
            ids = list_id.filter((v) => v !== null && v !== undefined);
        } else if (Array.isArray(list_id_of_places)) {
            ids = list_id_of_places.filter((v) => v !== null && v !== undefined);
        } else if (list_id !== null && list_id !== undefined) {
            ids = [list_id];
        } else if (list_id_of_places !== null && list_id_of_places !== undefined) {
            ids = [list_id_of_places];
        }

        if (!ids.length) {
            return res.status(400).json({ success: false, message: "Missing list_id or list_id_of_places in request body" });
        }

        const db = new sqlite3.Database(DB_PATH, sqlite3.OPEN_READONLY, (err) => {
            if (err) {
                return res.status(500).json({ success: false, message: "Failed to open static database", error: err.message });
            }
        });

        const placeholders = ids.map(() => "?").join(",");
        const sql = `SELECT rowid, * FROM places_new WHERE rowid IN (${placeholders})`;

        db.all(sql, ids, (err, rows) => {
            if (err) {
                db.close();
                return res.status(500).json({ success: false, message: "Error querying database", error: err.message });
            }
            db.close();
            const rowsMap = new Map();
            rows.forEach(row => {
                rowsMap.set(row.rowid, row); 
            });

            const orderedRows = ids.map(id => rowsMap.get(id)).filter(item => item !== undefined);
            return res.json({ success: true, count: orderedRows.length, data: orderedRows });
        });
    } catch (error) {
        return res.status(500).json({ success: false, message: "Error querying static database", error: error.message });
    }
};