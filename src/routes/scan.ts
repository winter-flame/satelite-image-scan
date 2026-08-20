import { Router } from "express";
import multer from "multer";

const router = Router();
const upload = multer({ dest: "uploads/" });

// POST /scan/upload  -- accepts an image, returns a placeholder scan result
router.post("/upload", upload.single("image"), (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: "No image uploaded" });
  }

  // TODO: replace with real satellite image processing
  const placeholderResult = {
    filename: req.file.originalname,
    sizeBytes: req.file.size,
    detections: [],
    status: "processed (placeholder)",
  };

  res.json(placeholderResult);
});

export default router;
