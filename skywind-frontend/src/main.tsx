import "leaflet/dist/leaflet.css";  //import css for map
import './index.css' //import style
import { StrictMode } from 'react' //this double run components
import { createRoot } from 'react-dom/client' //import the React DOM
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)

//document.getElementById('root') -> Gets the <div id="root"></div> from your index.html.
//! - tell trust me, this elem exist