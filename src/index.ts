import express from "express";
import scanRouter from "./routes/scan";

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());

app.get("/health", (_req, res) => {
  res.json({ status: "ok" });
});

app.use("/scan", scanRouter);

app.listen(PORT, () => {
  console.log(`satelite-image-scan listening on port ${PORT}`);
});
