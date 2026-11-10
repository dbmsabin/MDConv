import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { ResultRow } from "./ResultRow";
import type { ConvertResult, ConverterName } from "@/types";

interface ResultListProps {
  results: ConvertResult[];
  onReorder: (oldIndex: number, newIndex: number) => void;
  onRename: (id: string, name: string) => void;
  onRemove: (id: string) => void;
  onAltConverter: (id: string, converter: ConverterName) => void;
}

export function ResultList({
  results,
  onReorder,
  onRename,
  onRemove,
  onAltConverter,
}: ResultListProps) {
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    if (!over || active.id === over.id) return;

    const oldIndex = results.findIndex((r) => r.id === active.id);
    const newIndex = results.findIndex((r) => r.id === over.id);
    if (oldIndex !== -1 && newIndex !== -1) {
      onReorder(oldIndex, newIndex);
    }
  }

  if (results.length === 0) return null;

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragEnd={handleDragEnd}
    >
      <SortableContext
        items={results.map((r) => r.id)}
        strategy={verticalListSortingStrategy}
      >
        <div className="flex flex-col gap-2">
          {results.map((result, index) => (
            <ResultRow
              key={result.id}
              result={result}
              index={index}
              onRename={onRename}
              onRemove={onRemove}
              onAltConverter={onAltConverter}
            />
          ))}
        </div>
      </SortableContext>
    </DndContext>
  );
}

