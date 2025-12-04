import { BrowserRouter, Routes, Route } from "react-router-dom";
import Navbar from "../components/Navbar";

import HomePage from "../pages/HomePage";
import GeneratePage from "../pages/GeneratePage";
import RegionPage from "../pages/RegionPage";
import SavedRegionsPage from "../pages/SavedRegionsPage";
import AboutPage from "../pages/AboutPage";
import ContactPage from "../pages/ContactPage";

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Navbar />

      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/generate" element={<GeneratePage />} />
        <Route path="/region/:id" element={<RegionPage />} />
        <Route path="/saved" element={<SavedRegionsPage />} />
        <Route path="/about" element={<AboutPage />} />
        <Route path="/contact" element={<ContactPage />} />
      </Routes>
    </BrowserRouter>
  );
}