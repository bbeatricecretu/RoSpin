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
}

export function MapLayerControl({ waterLayerRef }: MapLayerControlProps) {
  const map = useMap();
  const [open, setOpen] = useState(false);
  const [showWater, setShowWater] = useState(false); // ON BY DEFAULT

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

  return (
    <div
      className="absolute top-[20px] left-[350px] z-[1000]
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
        </CollapsibleContent>
      </Collapsible>
    </div>
  );
}
