"use client";

import { useState, useEffect } from "react";
import { useMap } from "react-leaflet";
import {
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent,
} from "@/components/ui/collapsible";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { ChevronsUpDown } from "lucide-react";
import L from "leaflet";

interface MapLayerControlProps {
  waterLayerRef: React.MutableRefObject<L.GeoJSON | null>;
  gridLinesLayerRef: React.MutableRefObject<L.GeoJSON | null>;
  gridSubstationsLayerRef: React.MutableRefObject<L.GeoJSON | null>;
  reliefLayerRef: React.MutableRefObject<L.TileLayer | null>;
  showAltitude: boolean;
  onAltitudeChange: (show: boolean) => void;
}

export function MapLayerControl({
  waterLayerRef,
  gridLinesLayerRef,
  gridSubstationsLayerRef,
  reliefLayerRef,
  showAltitude,
  onAltitudeChange,
}: MapLayerControlProps) {

  const map = useMap();
  const [open, setOpen] = useState(false);
  const [showWater, setShowWater] = useState(false); // ON BY DEFAULT
  const [showGrid, setShowGrid] = useState(false);
  const [showRelief, setShowRelief] = useState(false);


  useEffect(() => {
    if (!map) return;

    const layer = waterLayerRef.current;
    if (!layer) return;

    if (showWater) map.addLayer(layer);
    else map.removeLayer(layer);

    return () => {
      if (layer && map.hasLayer(layer)) {
        map.removeLayer(layer);
      }
    };
  }, [showWater, waterLayerRef, map]);

  useEffect(() => {
    if (!map) return;

    const linesLayer = gridLinesLayerRef.current;
    const subsLayer = gridSubstationsLayerRef.current;

    if (showGrid) {
      if (linesLayer && !map.hasLayer(linesLayer)) {
        map.addLayer(linesLayer);
      }
      if (subsLayer && !map.hasLayer(subsLayer)) {
        map.addLayer(subsLayer);
      }
    } else {
      if (linesLayer && map.hasLayer(linesLayer)) {
        map.removeLayer(linesLayer);
      }
      if (subsLayer && map.hasLayer(subsLayer)) {
        map.removeLayer(subsLayer);
      }
    }

    return () => {
      if (linesLayer && map.hasLayer(linesLayer)) {
        map.removeLayer(linesLayer);
      }
      if (subsLayer && map.hasLayer(subsLayer)) {
        map.removeLayer(subsLayer);
      }
    };
  }, [showGrid, gridLinesLayerRef, gridSubstationsLayerRef, map]);

  useEffect(() => {
    if (!map) return;

    const layer = reliefLayerRef.current;
    if (!layer) return;

    if (showRelief) {
      map.addLayer(layer);
    } else if (map.hasLayer(layer)) {
      map.removeLayer(layer);
    }

    return () => {
      if (layer && map.hasLayer(layer)) {
        map.removeLayer(layer);
      }
    };
  }, [showRelief, reliefLayerRef, map]);


  return (
    <div
      className="absolute top-[20px] left-[400px] z-[1000]
      rounded-md border bg-white shadow p-2
      w-[100px] text-sm"
    >
      <Collapsible open={open} onOpenChange={setOpen}>
        <div className="flex items-center justify-between">
          <span className="font-semibold">Layers</span>

          <CollapsibleTrigger asChild>
            <Button variant="ghost" size="icon" className="h-5 w-5">
              <ChevronsUpDown size={14} />
            </Button>
          </CollapsibleTrigger>
        </div>

        <CollapsibleContent className="mt-2 flex flex-col gap-2">
          <div className="flex items-center gap-2">
            <Checkbox
              id="water-layer"
              checked={showWater}
              onCheckedChange={(checked: boolean | "indeterminate") => setShowWater(checked === true)}
            />
            <label htmlFor="water-layer" className="text-xs">
              Water
            </label>
          </div>
          <div className="flex items-center gap-2">
            <Checkbox
              id="grid-layer"
              checked={showGrid}
              onCheckedChange={(checked: boolean | "indeterminate") => setShowGrid(checked === true)}
            />
            <label htmlFor="grid-layer" className="text-xs">
              Grid
            </label>
          </div>
          <div className="flex items-center gap-2">
            <Checkbox
              id="relief-layer"
              checked={showRelief}
              onCheckedChange={(checked: boolean | "indeterminate") =>
                setShowRelief(checked === true)
              }
            />
            <label htmlFor="relief-layer" className="text-xs">
              Relief
            </label>
          </div>
          <div className="flex items-center gap-2">
            <Checkbox
              id="altitude-layer"
              checked={showAltitude}
              onCheckedChange={(checked: boolean | "indeterminate") =>
                onAltitudeChange(checked === true)
              }
            />
            <label htmlFor="altitude-layer" className="text-xs">
              Altitude
            </label>
          </div>

        </CollapsibleContent>
      </Collapsible>
    </div>
  );
}
