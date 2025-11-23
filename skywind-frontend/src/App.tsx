import { BrowserRouter, Routes, Route } from "react-router-dom";
//BrowserROuter-enables navigation without page reload
//Routes-container for <Route> entries
//Route-define one url

import HomePage from "./pages/HomePage";
import RegionPage from "./pages/RegionPage";

//App-the brain controlling which page appears
function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/region" element={<RegionPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
//allows other files(main.tsx) to import this component