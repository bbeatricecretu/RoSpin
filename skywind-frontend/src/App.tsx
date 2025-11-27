import { BrowserRouter, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import HomePage from "./pages/HomePage";
import RegionPage from "./pages/RegionPage";

function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/region" element={<RegionPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
//allows other files(main.tsx) to import this component