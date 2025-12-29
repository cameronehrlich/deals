"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  GitBranch,
  Building,
  ChevronRight,
  ChevronDown,
  FileText,
  DollarSign,
  CheckCircle2,
  Circle,
  Clock,
  AlertCircle,
  Plus,
  MoreHorizontal,
} from "lucide-react";
import { api, PipelineOverview, PipelineProperty, DealStage, Offer } from "@/lib/api";
import { LoadingPage } from "@/components/LoadingSpinner";
import { cn, formatCurrency } from "@/lib/utils";
import { ScoreGauge } from "@/components/ScoreGauge";

// Stage colors for visual distinction
const STAGE_COLORS: Record<string, string> = {
  researching: "bg-gray-100 border-gray-300",
  contacted: "bg-blue-50 border-blue-200",
  viewing: "bg-purple-50 border-purple-200",
  analyzing: "bg-indigo-50 border-indigo-200",
  offer_prep: "bg-amber-50 border-amber-200",
  offer_submitted: "bg-orange-50 border-orange-200",
  negotiating: "bg-yellow-50 border-yellow-200",
  under_contract: "bg-emerald-50 border-emerald-200",
  due_diligence: "bg-teal-50 border-teal-200",
  closing: "bg-green-50 border-green-200",
  closed: "bg-green-100 border-green-300",
  lost: "bg-red-50 border-red-200",
  none: "bg-gray-50 border-gray-200",
};

const STAGE_HEADER_COLORS: Record<string, string> = {
  researching: "bg-gray-500",
  contacted: "bg-blue-500",
  viewing: "bg-purple-500",
  analyzing: "bg-indigo-500",
  offer_prep: "bg-amber-500",
  offer_submitted: "bg-orange-500",
  negotiating: "bg-yellow-500",
  under_contract: "bg-emerald-500",
  due_diligence: "bg-teal-500",
  closing: "bg-green-500",
  closed: "bg-green-600",
  lost: "bg-red-500",
  none: "bg-gray-400",
};

// Property card in pipeline view
function PipelinePropertyCard({
  property,
  onClick,
  onMoveToStage,
  stages,
  onDragStart,
}: {
  property: PipelineProperty;
  onClick: () => void;
  onMoveToStage: (stage: string) => void;
  stages: DealStage[];
  onDragStart: (e: React.DragEvent, propertyId: string) => void;
}) {
  const [showStageMenu, setShowStageMenu] = useState(false);

  const handleDragStart = (e: React.DragEvent) => {
    onDragStart(e, property.id);
    e.dataTransfer.effectAllowed = "move";
  };

  return (
    <div
      draggable
      onDragStart={handleDragStart}
      className={cn(
        "bg-white rounded-lg border shadow-sm p-3 cursor-grab hover:shadow-md transition-shadow relative",
        "active:cursor-grabbing active:opacity-50",
        property.has_active_offer && "ring-2 ring-amber-400"
      )}
    >
      {/* Photo thumbnail */}
      {property.primary_photo && (
        <div className="w-full h-24 rounded-md overflow-hidden mb-2">
          <img
            src={property.primary_photo}
            alt={property.address}
            className="w-full h-full object-cover"
          />
        </div>
      )}

      {/* Address */}
      <div onClick={onClick} className="mb-2">
        <h4 className="font-medium text-sm text-gray-900 truncate">
          {property.address}
        </h4>
        <p className="text-xs text-gray-500">
          {property.city}, {property.state}
        </p>
      </div>

      {/* Price & Score */}
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-semibold text-gray-900">
          {property.list_price ? formatCurrency(property.list_price) : "N/A"}
        </span>
        {property.deal_score && (
          <span
            className={cn(
              "text-xs font-medium px-2 py-0.5 rounded-full",
              property.deal_score >= 70
                ? "bg-green-100 text-green-700"
                : property.deal_score >= 50
                ? "bg-amber-100 text-amber-700"
                : "bg-red-100 text-red-700"
            )}
          >
            {property.deal_score}
          </span>
        )}
      </div>

      {/* Badges */}
      <div className="flex items-center gap-2 text-xs">
        {property.has_active_offer && (
          <span className="inline-flex items-center gap-1 text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full">
            <FileText className="h-3 w-3" />
            Offer
          </span>
        )}
        {property.days_in_stage !== null && property.days_in_stage !== undefined && (
          <span className="inline-flex items-center gap-1 text-gray-500">
            <Clock className="h-3 w-3" />
            {property.days_in_stage}d
          </span>
        )}
      </div>

      {/* Quick stage move menu */}
      <div className="absolute top-2 right-2">
        <button
          onClick={(e) => {
            e.stopPropagation();
            setShowStageMenu(!showStageMenu);
          }}
          className="p-1 hover:bg-gray-100 rounded"
        >
          <MoreHorizontal className="h-4 w-4 text-gray-400" />
        </button>
        {showStageMenu && (
          <div className="absolute right-0 mt-1 w-48 bg-white border rounded-lg shadow-lg z-10 py-1 max-h-64 overflow-y-auto">
            <p className="px-3 py-1 text-xs text-gray-500 font-medium">Move to...</p>
            {stages.map((stage) => (
              <button
                key={stage.id}
                onClick={(e) => {
                  e.stopPropagation();
                  onMoveToStage(stage.id);
                  setShowStageMenu(false);
                }}
                className={cn(
                  "w-full text-left px-3 py-1.5 text-sm hover:bg-gray-100",
                  property.deal_stage === stage.id && "bg-gray-50 font-medium"
                )}
              >
                {stage.name}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// Stage column
function StageColumn({
  stage,
  properties,
  isCollapsed,
  onToggleCollapse,
  onPropertyClick,
  onMoveProperty,
  allStages,
  onDragStart,
  onDrop,
  isDragTarget,
  onDragEnter,
  onDragLeave,
}: {
  stage: DealStage;
  properties: PipelineProperty[];
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  onPropertyClick: (id: string) => void;
  onMoveProperty: (propertyId: string, stage: string) => void;
  allStages: DealStage[];
  onDragStart: (e: React.DragEvent, propertyId: string) => void;
  onDrop: (e: React.DragEvent, stageId: string) => void;
  isDragTarget: boolean;
  onDragEnter?: (stageId: string) => void;
  onDragLeave?: () => void;
}) {
  const stageColor = STAGE_COLORS[stage.id] || STAGE_COLORS.none;
  const headerColor = STAGE_HEADER_COLORS[stage.id] || STAGE_HEADER_COLORS.none;

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
  };

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    onDragEnter?.(stage.id);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    // Only trigger leave if we're leaving the column entirely
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
    if (
      e.clientX < rect.left ||
      e.clientX > rect.right ||
      e.clientY < rect.top ||
      e.clientY > rect.bottom
    ) {
      onDragLeave?.();
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    onDrop(e, stage.id);
  };

  if (isCollapsed) {
    return (
      <div
        onDragOver={handleDragOver}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={cn(
          "flex-shrink-0 w-12 rounded-lg border cursor-pointer transition-all",
          stageColor,
          isDragTarget && "ring-2 ring-primary-400 ring-offset-2"
        )}
        onClick={onToggleCollapse}
      >
        <div className={cn("h-2 rounded-t-lg", headerColor)} />
        <div className="p-2 text-center">
          <span className="writing-mode-vertical text-xs font-medium text-gray-600">
            {stage.name}
          </span>
          <span className="block text-xs text-gray-400 mt-2">
            {properties.length}
          </span>
        </div>
      </div>
    );
  }

  return (
    <div
      onDragOver={handleDragOver}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={cn(
        "flex-shrink-0 w-72 rounded-lg border transition-all",
        stageColor,
        isDragTarget && "ring-2 ring-primary-400 ring-offset-2"
      )}
    >
      {/* Header */}
      <div className={cn("h-2 rounded-t-lg", headerColor)} />
      <div
        className="flex items-center justify-between p-3 border-b cursor-pointer"
        onClick={onToggleCollapse}
      >
        <div className="flex items-center gap-2">
          <span className="font-medium text-sm">{stage.name}</span>
          <span className="text-xs text-gray-500 bg-white px-2 py-0.5 rounded-full">
            {properties.length}
          </span>
        </div>
        <ChevronDown className="h-4 w-4 text-gray-400" />
      </div>

      {/* Properties */}
      <div className="p-2 space-y-2 max-h-[calc(100vh-280px)] overflow-y-auto min-h-[100px]">
        {properties.length === 0 ? (
          <div className={cn(
            "text-center py-8 text-gray-400 text-sm rounded-lg border-2 border-dashed",
            isDragTarget ? "border-primary-400 bg-primary-50" : "border-transparent"
          )}>
            {isDragTarget ? "Drop here" : "No properties"}
          </div>
        ) : (
          properties.map((property) => (
            <PipelinePropertyCard
              key={property.id}
              property={property}
              onClick={() => onPropertyClick(property.id)}
              onMoveToStage={(newStage) => onMoveProperty(property.id, newStage)}
              stages={allStages}
              onDragStart={onDragStart}
            />
          ))
        )}
      </div>
    </div>
  );
}

// Stats bar
function PipelineStats({
  overview,
}: {
  overview: PipelineOverview;
}) {
  return (
    <div className="flex gap-6 text-sm">
      <div className="flex items-center gap-2">
        <Building className="h-4 w-4 text-gray-400" />
        <span className="text-gray-600">
          <span className="font-semibold text-gray-900">{overview.total_properties}</span>{" "}
          properties
        </span>
      </div>
      <div className="flex items-center gap-2">
        <FileText className="h-4 w-4 text-amber-500" />
        <span className="text-gray-600">
          <span className="font-semibold text-gray-900">{overview.active_offers}</span>{" "}
          active offers
        </span>
      </div>
      <div className="flex items-center gap-2">
        <CheckCircle2 className="h-4 w-4 text-green-500" />
        <span className="text-gray-600">
          <span className="font-semibold text-gray-900">{overview.under_contract}</span>{" "}
          under contract
        </span>
      </div>
    </div>
  );
}

// Empty state
function PipelineEmpty() {
  return (
    <div className="card text-center py-16 animate-fade-in">
      <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary-100 mb-6">
        <GitBranch className="h-8 w-8 text-primary-600" />
      </div>
      <h3 className="text-xl font-semibold text-gray-900 mb-2">No Properties in Pipeline</h3>
      <p className="text-gray-500 max-w-md mx-auto mb-6">
        Save properties and move them through deal stages to track your investment pipeline.
      </p>
      <div className="flex flex-col sm:flex-row gap-3 justify-center">
        <a href="/deals" className="btn-primary inline-flex items-center gap-2">
          <Building className="h-4 w-4" />
          Find Properties
        </a>
        <a href="/saved" className="btn-outline inline-flex items-center gap-2">
          <FileText className="h-4 w-4" />
          View Saved
        </a>
      </div>
    </div>
  );
}

export default function PipelinePage() {
  const router = useRouter();
  const [overview, setOverview] = useState<PipelineOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [collapsedStages, setCollapsedStages] = useState<Set<string>>(new Set());

  // Drag-and-drop state
  const [draggingPropertyId, setDraggingPropertyId] = useState<string | null>(null);
  const [dragOverStage, setDragOverStage] = useState<string | null>(null);

  // Only show stages that have properties or are key stages
  const KEY_STAGES = new Set([
    "researching",
    "contacted",
    "offer_prep",
    "offer_submitted",
    "under_contract",
    "closed",
    "lost",
  ]);

  // Fetch pipeline overview
  const fetchPipeline = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getPipelineOverview();
      setOverview(data);
    } catch (err) {
      console.error("Failed to fetch pipeline:", err);
      setError(err instanceof Error ? err.message : "Failed to load pipeline");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPipeline();
  }, [fetchPipeline]);

  // Toggle stage collapse
  const toggleStageCollapse = (stageId: string) => {
    setCollapsedStages((prev) => {
      const next = new Set(prev);
      if (next.has(stageId)) {
        next.delete(stageId);
      } else {
        next.add(stageId);
      }
      return next;
    });
  };

  // Handle property click
  const handlePropertyClick = (propertyId: string) => {
    router.push(`/saved/${propertyId}`);
  };

  // Handle move property to stage
  const handleMoveProperty = async (propertyId: string, newStage: string) => {
    try {
      await api.updatePropertyStage(propertyId, newStage);
      // Refresh pipeline
      fetchPipeline();
    } catch (err) {
      console.error("Failed to move property:", err);
    }
  };

  // Drag-and-drop handlers
  const handleDragStart = (e: React.DragEvent, propertyId: string) => {
    setDraggingPropertyId(propertyId);
    e.dataTransfer.setData("text/plain", propertyId);
  };

  const handleDragEnter = (stageId: string) => {
    if (draggingPropertyId) {
      setDragOverStage(stageId);
    }
  };

  const handleDrop = async (e: React.DragEvent, stageId: string) => {
    e.preventDefault();
    const propertyId = e.dataTransfer.getData("text/plain") || draggingPropertyId;
    if (propertyId && stageId) {
      await handleMoveProperty(propertyId, stageId);
    }
    setDraggingPropertyId(null);
    setDragOverStage(null);
  };

  const handleDragEnd = () => {
    setDraggingPropertyId(null);
    setDragOverStage(null);
  };

  // Filter stages to show
  const stagesToShow = overview?.stages.filter((stage) => {
    const properties = overview.properties_by_stage[stage.id] || [];
    return properties.length > 0 || KEY_STAGES.has(stage.id);
  }) || [];

  if (loading) {
    return <LoadingPage />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Deal Pipeline</h1>
          <p className="text-gray-500 mt-1">
            Track your properties through the investment process
          </p>
        </div>
        {overview && <PipelineStats overview={overview} />}
      </div>

      {error && (
        <div className="card border-red-200 bg-red-50">
          <p className="text-red-700">{error}</p>
          <button onClick={fetchPipeline} className="btn-primary mt-3">
            Retry
          </button>
        </div>
      )}

      {overview && overview.total_properties === 0 ? (
        <PipelineEmpty />
      ) : (
        <div className="flex gap-4 overflow-x-auto pb-4">
          {/* Unstaged column */}
          {overview && (overview.properties_by_stage["none"]?.length > 0) && (
            <StageColumn
              stage={{ id: "none", name: "Not Staged", order: 0 }}
              properties={overview.properties_by_stage["none"] || []}
              isCollapsed={collapsedStages.has("none")}
              onToggleCollapse={() => toggleStageCollapse("none")}
              onPropertyClick={handlePropertyClick}
              onMoveProperty={handleMoveProperty}
              allStages={overview.stages}
              onDragStart={handleDragStart}
              onDrop={handleDrop}
              isDragTarget={dragOverStage === "none"}
              onDragEnter={setDragOverStage}
              onDragLeave={() => setDragOverStage(null)}
            />
          )}

          {/* Stage columns */}
          {stagesToShow.map((stage) => (
            <StageColumn
              key={stage.id}
              stage={stage}
              properties={overview?.properties_by_stage[stage.id] || []}
              isCollapsed={collapsedStages.has(stage.id)}
              onToggleCollapse={() => toggleStageCollapse(stage.id)}
              onPropertyClick={handlePropertyClick}
              onMoveProperty={handleMoveProperty}
              allStages={overview?.stages || []}
              onDragStart={handleDragStart}
              onDrop={handleDrop}
              isDragTarget={dragOverStage === stage.id}
              onDragEnter={setDragOverStage}
              onDragLeave={() => setDragOverStage(null)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
