import {queryStaticDB} from "../controllers/query_static_db.js";
import express from "express";

const queryStaticDBRoutes = express.Router();

queryStaticDBRoutes.post("/query", queryStaticDB);

export default queryStaticDBRoutes;