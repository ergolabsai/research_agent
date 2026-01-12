import React, { useState } from "react";
import {
  FileText,
  Target,
  Upload,
  X,
  CheckCircle,
  AlertCircle,
  Edit2,
  Save,
  XCircle,
  Image as ImageIcon,
  ChevronDown,
  ChevronRight,
  MessageSquare,
} from "lucide-react";

import { Routes, Route, Link } from "react-router-dom";
import { Box, Typography } from "@mui/material";
import { ThemeMode } from "./theme";
import Settings from "./Settings";

// EditableTextItem Component
function EditableTextItem({
  text,
  itemId,
  annotation,
  onStatusChange,
  onTextChange,
  isEditing,
  onStartEdit,
  onCancelEdit,
}: any) {
  const [localText, setLocalText] = useState(text);
  const status = annotation?.status || "default";
  const editedText = annotation?.editedText;

  React.useEffect(() => {
    setLocalText(editedText || text);
  }, [editedText, text]);

  const handleSave = () => {
    onTextChange(itemId, localText);
  };

  const handleCancel = () => {
    setLocalText(editedText || text);
    onCancelEdit(itemId);
  };

  // Determine styling based on status
  const getItemStyle = () => {
    if (status === "dismissed") {
      return "bg-gray-100 opacity-60";
    } else if (status === "important") {
      return "bg-yellow-100 border-yellow-400";
    }
    return "bg-white";
  };

  const getTextStyle = () => {
    if (status === "dismissed") {
      return "text-gray-500 line-through";
    } else if (status === "important") {
      return "text-gray-900 font-medium";
    }
    return "text-gray-700";
  };

  return (
    <Box>
      {isEditing ? (
        <Box>
          <textarea
            value={localText}
            onChange={(e) => setLocalText(e.target.value)}
            rows={4}
          />
          <Box>
            <button onClick={handleSave}>
              <Save />
              Save
            </button>
            <button onClick={handleCancel}>Cancel</button>
          </Box>
        </Box>
      ) : (
        <>
          <p>{editedText || text}</p>

          {/* Action Buttons */}
          <Box>
            <button
              onClick={() =>
                onStatusChange(
                  itemId,
                  status === "dismissed" ? "default" : "dismissed"
                )
              }
            >
              {status === "dismissed" ? "Undismiss" : "Dismiss"}
            </button>
            <button
              onClick={() =>
                onStatusChange(
                  itemId,
                  status === "important" ? "default" : "important"
                )
              }
            >
              {status === "important" ? "Unmark" : "Important"}
            </button>
            <button onClick={() => onStartEdit(itemId)}>
              <Edit2 />
              Edit
            </button>
          </Box>
        </>
      )}
    </Box>
  );
}

// AnnotationSection Component
function AnnotationSection({
  title,
  items,
  icon,
  imageName,
  sectionType,
  isExpanded,
  onToggleExpand,
  annotations,
  onStatusChange,
  onTextChange,
  editingItems,
  onStartEdit,
  onCancelEdit,
}: any) {
  const colorClass =
    sectionType === "similarities" ? "text-green-700" : "text-orange-700";
  const bgClass =
    sectionType === "similarities" ? "bg-green-50" : "bg-orange-50";
  const borderClass =
    sectionType === "similarities" ? "border-green-200" : "border-orange-200";

  return (
    <Box>
      {/* Header */}
      <button onClick={onToggleExpand}>
        <Box>
          {icon}
          <h4>
            {title} ({items.length})
          </h4>
        </Box>
        {isExpanded ? <ChevronDown /> : <ChevronRight />}
      </button>

      {/* Items List */}
      {isExpanded && (
        <Box>
          {items.length === 0 ? (
            <p>No items to display</p>
          ) : (
            items.map((item: any, idx: number) => {
              const itemId = `${imageName}-${sectionType}-${idx}`;
              return (
                <EditableTextItem
                  key={itemId}
                  text={item}
                  itemId={itemId}
                  annotation={annotations[itemId]}
                  onStatusChange={onStatusChange}
                  onTextChange={onTextChange}
                  isEditing={editingItems[itemId]}
                  onStartEdit={onStartEdit}
                  onCancelEdit={onCancelEdit}
                />
              );
            })
          )}
        </Box>
      )}
    </Box>
  );
}

function PaperEditor() {
  const [draft, setDraft] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [images, setImages] = useState([]);
  const [error, setError] = useState(null);
  const [checkedItems, setCheckedItems] = useState({});
  const [editingItems, setEditingItems] = useState({});
  const [editedTexts, setEditedTexts] = useState({});
  const [comparisonResults, setComparisonResults] = useState(null);
  const [finalReview, setFinalReview] = useState(null);

  // New state for annotations
  const [expandedSections, setExpandedSections] = useState({});
  const [annotations, setAnnotations] = useState({});

  // Parse text into individual items
  // const parseItems = (text) => {
  //   if (!text) return [];
  //   // Split by newlines, bullet points, or numbered lists
  //   return text
  //     .split(/\n+/)
  //     .map((item) =>
  //       item
  //         .replace(/^[-•*]\s*/, "")
  //         .replace(/^\d+\.\s*/, "")
  //         .trim()
  //     )
  //     .filter((item) => item.length > 0);
  // };

  // Toggle section expand/collapse
  const toggleSection = (imageName: any, sectionType: any) => {
    const key = `${imageName}-${sectionType}`;
    setExpandedSections((prev: any) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  // Handle status changes (dismiss/important)
  const handleStatusChange = (itemId: any, newStatus: any) => {
    setAnnotations((prev: any) => ({
      ...prev,
      [itemId]: {
        ...prev[itemId],
        status: newStatus,
        timestamp: new Date().toISOString(),
      },
    }));
  };

  // Handle note changes
  const handleTextChange = (itemId: any, newText: any) => {
    setAnnotations((prev: any) => ({
      ...prev,
      [itemId]: {
        ...prev[itemId],
        editedText: newText,
        timestamp: new Date().toISOString(),
      },
    }));
    // Close editing mode after saving
    setEditingItems((prev) => ({
      ...prev,
      [itemId]: false,
    }));
  };

  // Start editing an item
  const handleStartEdit = (itemId: any) => {
    setEditingItems((prev) => ({
      ...prev,
      [itemId]: true,
    }));
  };

  // Cancel editing an item
  const handleCancelEdit = (itemId: any) => {
    setEditingItems((prev) => ({
      ...prev,
      [itemId]: false,
    }));
  };

  // Refine figure analysis with annotations
  const refineFigureAnalysis = async () => {
    if (Object.keys(annotations).length === 0) {
      // setError("Please add at least one annotation before refining");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Process similarities and differences for each image
      const processedFigures = images.map((img: any, imgIndex: number) => {
        const similarities =
          comparisonResults.figure_similarities?.[imgIndex] || [];
        const differences =
          comparisonResults.figure_differences?.[imgIndex] || [];

        // Helper function to process items (filter dismissed, apply edits, mark important)
        const processItems = (items: any, sectionType: any) => {
          return items
            .map((item: any, idx: number) => {
              const itemId = `${img.name}-${sectionType}-${idx}`;
              const annotation = annotations[itemId];

              // Skip dismissed items
              if (annotation?.status === "dismissed") {
                return null;
              }

              // Use edited text if available, otherwise original
              const text = annotation?.editedText || item;

              // Check if marked as important
              const isImportant = annotation?.status === "important";

              return {
                text: text,
                important: isImportant,
                originalIndex: idx,
              };
            })
            .filter((item: any) => item !== null); // Remove dismissed items
        };

        const processedSimilarities = processItems(
          similarities,
          "similarities"
        );
        const processedDifferences = processItems(differences, "differences");

        // Get indices of important items in the filtered arrays
        const importantSimilarityIndices = processedSimilarities
          .map((item, idx) => (item.important ? idx : -1))
          .filter((idx) => idx !== -1);

        const importantDifferenceIndices = processedDifferences
          .map((item, idx) => (item.important ? idx : -1))
          .filter((idx) => idx !== -1);

        return {
          imageName: img.name,
          similarities: processedSimilarities.map((item) => item.text),
          differences: processedDifferences.map((item) => item.text),
          importantSimilarities: importantSimilarityIndices,
          importantDifferences: importantDifferenceIndices,
        };
      });

      const response = await fetch(
        "http://localhost:5001/api/refine_figure_analysis",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            apiKey: apiKey,
            draft: draft,
            context: result?.context || "",
            processedFigures: processedFigures,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || `Server error: ${response.status}`);
      }

      console.log("Refined analysis response:", data);

      // Store the final review
      if (data.success && data.review) {
        setFinalReview(data.review);
      }

      // Update with refined results
      setComparisonResults(data);

      // Clear annotations after successful refinement
      setAnnotations({});
      setEditingItems({});
    } catch (err: any) {
      setError(err.message);
      console.error("Error refining analysis:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleImageUpload = async (e) => {
    const files = Array.from(e.target.files);

    // Convert images to base64
    const imagePromises = files.map((file) => {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
          resolve({
            name: file.name,
            type: file.type,
            data: reader.result.split(",")[1],
            preview: reader.result,
          });
        };
        reader.onerror = reject;
        reader.readAsDataURL(file);
      });
    });

    try {
      const newImages = await Promise.all(imagePromises);
      setImages([...images, ...newImages]);
    } catch (error) {
      console.error("Error loading images:", error);
      setError("Failed to load images. Please try again.");
    }
  };

  const removeImage = (index) => {
    setImages(images.filter((_, i) => i !== index));
  };

  const createContext = async () => {
    setLoading(true);
    setResult(null);
    setError(null);
    setCheckedItems({});

    try {
      const response = await fetch("http://localhost:5001/api/create_context", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          apiKey: apiKey,
          draft: draft,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || `Server error: ${response.status}`);
      }

      setResult(data);
      // Initialize all items as checked
      const initialChecked = {};
      if (data.items) {
        data.items.forEach((item) => {
          initialChecked[item.id] = true;
        });
      }
      setCheckedItems(initialChecked);
    } catch (err) {
      setError(err.message);
      console.error("Error:", err);
    } finally {
      setLoading(false);
    }
  };

  const toggleItem = (itemId) => {
    setCheckedItems((prev) => ({
      ...prev,
      [itemId]: !prev[itemId],
    }));
  };

  const toggleAll = (checked) => {
    const newChecked = {};
    if (result?.items) {
      result.items.forEach((item) => {
        newChecked[item.id] = checked;
      });
    }
    setCheckedItems(newChecked);
  };

  const startEditing = (itemId, currentText) => {
    setEditingItems((prev) => ({ ...prev, [itemId]: true }));
    setEditedTexts((prev) => ({ ...prev, [itemId]: currentText }));
  };

  const cancelEditing = (itemId) => {
    setEditingItems((prev) => ({ ...prev, [itemId]: false }));
    setEditedTexts((prev) => {
      const newTexts = { ...prev };
      delete newTexts[itemId];
      return newTexts;
    });
  };

  const saveEdit = (itemId) => {
    if (!result?.items) return;

    const updatedItems = result.items.map((item) =>
      item.id === itemId ? { ...item, text: editedTexts[itemId] } : item
    );

    setResult({ ...result, items: updatedItems });
    setEditingItems((prev) => ({ ...prev, [itemId]: false }));
  };

  const refineContext = async () => {
    if (!result?.items) return;

    const checkedItemsList = result.items.filter(
      (item) => checkedItems[item.id]
    );

    if (checkedItemsList.length === 0) {
      setError("Please select at least one item to send");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch("http://localhost:5001/api/refine_context", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          apiKey: apiKey,
          selectedItems: checkedItemsList,
          draft: draft,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || `Server error: ${response.status}`);
      }

      // Handle the response from the agent
      console.log("Agent response:", data);

      // Update result with the refined context
      setResult((prev) => ({
        ...prev,
        context: data.context,
      }));
    } catch (err) {
      setError(err.message);
      console.error("Error sending to agent:", err);
    } finally {
      setLoading(false);
    }
  };

  const analyzeImages = async () => {
    if (images.length === 0) return;

    // Check if we have refined context available
    if (!result?.context) {
      setError("Please refine context before analyzing images");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch("http://localhost:5001/api/analyze_images", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          apiKey: apiKey,
          draft: draft,
          context: result.context,
          images: images.map((img) => ({
            type: img.type,
            data: img.data,
            name: img.name,
          })),
        }),
      });

      const data = await response.json();

      console.log("Full response:", data);
      console.log("Figure Differences:", data.figure_differences);
      console.log("Figure Similarities:", data.figure_similarities);
      console.log("Type of figureDifferences:", typeof data.figure_differences);
      console.log("Is array?:", Array.isArray(data.figure_differences));

      if (!response.ok) {
        throw new Error(data.error || `Server error: ${response.status}`);
      }

      console.log("Image analysis response:", data);

      // Store the comparison results
      setComparisonResults(data);

      // Initialize all sections as expanded
      const initialExpanded = {};
      images.forEach((img, index) => {
        initialExpanded[`${img.name}-similarities`] = true;
        initialExpanded[`${img.name}-differences`] = true;
      });
      setExpandedSections(initialExpanded);
    } catch (err) {
      setError(err.message);
      console.error("Error analyzing images:", err);
    } finally {
      setLoading(false);
    }
  };

  const FinalReview = () => {
    return (
      <Box>
        <Box>
          <MessageSquare />
          <h2>Final Review</h2>
        </Box>
        <Box>
          <Box>
            <p>{finalReview}</p>
          </Box>
        </Box>
      </Box>
    );
  };

  const ComparisonResults = () => {
    return (
      <Box>
        <Box>
          <ImageIcon />
          <h2>Figure Analysis</h2>
        </Box>

        <Box>
          {images.map((originalImage, index) => {
            const expectedImageData =
              comparisonResults.expected_images?.[index];
            const mediaType = comparisonResults.expected_media_types?.[index];
            const similarityItems =
              comparisonResults.figure_similarities?.[index] || [];
            const differenceItems =
              comparisonResults.figure_differences?.[index] || [];

            return (
              <Box key={index}>
                <h3>{originalImage.name}</h3>

                {/* Side-by-side images */}
                <Box>
                  {/* Original Image */}
                  <Box>
                    <h4>Original Figure</h4>
                    <Box>
                      <img
                        src={originalImage.preview}
                        alt={`Original ${originalImage.name}`}
                      />
                    </Box>
                  </Box>

                  {/* Expected Image */}
                  <Box>
                    <h4>Expected Figure (Generated)</h4>
                    <Box>
                      {expectedImageData && mediaType ? (
                        <img
                          src={`data:${mediaType};base64,${expectedImageData}`}
                          alt={`Expected ${originalImage.name}`}
                        />
                      ) : (
                        <Box>No expected image generated</Box>
                      )}
                    </Box>
                  </Box>
                </Box>

                {/* Similarities and Differences - Collapsible */}
                <Box>
                  {/* Similarities Section */}
                  <AnnotationSection
                    title="Similarities"
                    items={similarityItems}
                    icon={<CheckCircle />}
                    imageName={originalImage.name}
                    sectionType="similarities"
                    isExpanded={
                      expandedSections[`${originalImage.name}-similarities`]
                    }
                    onToggleExpand={() =>
                      toggleSection(originalImage.name, "similarities")
                    }
                    annotations={annotations}
                    onStatusChange={handleStatusChange}
                    onTextChange={handleTextChange}
                    editingItems={editingItems}
                    onStartEdit={handleStartEdit}
                    onCancelEdit={handleCancelEdit}
                  />

                  {/* Differences Section */}
                  <AnnotationSection
                    title="Differences"
                    items={differenceItems}
                    icon={<AlertCircle />}
                    imageName={originalImage.name}
                    sectionType="differences"
                    isExpanded={
                      expandedSections[`${originalImage.name}-differences`]
                    }
                    onToggleExpand={() =>
                      toggleSection(originalImage.name, "differences")
                    }
                    annotations={annotations}
                    onStatusChange={handleStatusChange}
                    onTextChange={handleTextChange}
                    editingItems={editingItems}
                    onStartEdit={handleStartEdit}
                    onCancelEdit={handleCancelEdit}
                  />
                </Box>
              </Box>
            );
          })}
        </Box>

        {/* Refine Figure Analysis Button */}
        <Box>
          <button
            onClick={refineFigureAnalysis}
            disabled={loading || Object.keys(annotations).length === 0}
          >
            {loading ? (
              <>
                <Box />
                Refining Analysis...
              </>
            ) : (
              <>
                <Target />
                Refine Figure Analysis ({Object.keys(annotations).length}{" "}
                annotations)
              </>
            )}
          </button>
        </Box>
      </Box>
    );
  };
  const ImageUpload = () => {
    return (
      <Box>
        <label>Upload Images (Optional)</label>

        <Box>
          <input
            type="file"
            id="image-upload"
            accept="image/*"
            multiple
            onChange={handleImageUpload}
          />
          <label htmlFor="image-upload">
            <Upload />
            <span>Click to upload images</span>
          </label>
        </Box>

        {images.length > 0 && (
          <Box>
            {images.map((image, index) => (
              <Box key={index}>
                <img src={image.preview} alt={image.name} />
                <button onClick={() => removeImage(index)}>
                  <X />
                </button>
              </Box>
            ))}
          </Box>
        )}

        {/* Analyze Images Button */}
        {images.length > 0 && (
          <button onClick={analyzeImages} disabled={loading}>
            {loading ? (
              <>
                <Box />
                Analyzing Images...
              </>
            ) : (
              <>
                <Target />
                Analyze Images
              </>
            )}
          </button>
        )}
      </Box>
    );
  };
  return (
    <Box>
      <Box>
        <Box>
          <h1>
            <FileText />
            Paper Review Assistant
          </h1>
          <p>AI-powered reviewing asistant</p>
        </Box>

        <Box>
          {/* Left Column - Input */}
          <Box>
            {/* API Key Input */}
            <Box>
              <label>Anthropic API Key</label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="sk-ant-..."
              />
            </Box>

            {/* Draft Text Input */}
            <Box style={{ height: "432px" }}>
              <label>Paper Draft</label>
              <textarea
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                placeholder="Paste your paper draft here..."
              />
            </Box>
          </Box>

          {/* Right Column - Context Results (Compact) */}
          <Box>
            {error && (
              <Box>
                <AlertCircle />
                <Box>
                  <h3>Error</h3>
                  <p>{error}</p>
                </Box>
              </Box>
            )}

            {/* Create Context Button */}
            <button
              onClick={createContext}
              disabled={!draft || !apiKey || loading}
            >
              {loading ? (
                <>
                  <Box />
                  Creating Context...
                </>
              ) : (
                <>
                  <Target />
                  Create Context
                </>
              )}
            </button>

            {result && result.success && result.items && (
              <Box style={{ height: "500px" }}>
                <Box>
                  <Box>
                    <CheckCircle />
                    <h2>Context</h2>
                  </Box>
                  <Box>
                    <span>
                      {Object.values(checkedItems).filter(Boolean).length} of{" "}
                      {result.items.length} selected
                    </span>
                  </Box>
                </Box>

                {/* Controls */}
                <Box>
                  <button onClick={() => toggleAll(true)}>Select All</button>
                  <button onClick={() => toggleAll(false)}>Deselect All</button>
                  <button
                    onClick={refineContext}
                    disabled={
                      Object.values(checkedItems).filter(Boolean).length ===
                        0 || loading
                    }
                  >
                    <Target />
                    Refine Context
                  </button>
                </Box>

                {/* Items List - COMPACT VERSION */}
                <Box>
                  {result.items.map((item) => (
                    <Box key={item.id}>
                      <Box>
                        <input
                          type="checkbox"
                          checked={checkedItems[item.id] || false}
                          onChange={() => toggleItem(item.id)}
                        />
                        <Box>
                          {editingItems[item.id] ? (
                            <Box>
                              <textarea
                                value={editedTexts[item.id] || item.text}
                                onChange={(e) =>
                                  setEditedTexts((prev) => ({
                                    ...prev,
                                    [item.id]: e.target.value,
                                  }))
                                }
                                rows={3}
                              />
                              <Box>
                                <button onClick={() => saveEdit(item.id)}>
                                  <Save />
                                  Save
                                </button>
                                <button onClick={() => cancelEditing(item.id)}>
                                  <XCircle />
                                  Cancel
                                </button>
                              </Box>
                            </Box>
                          ) : (
                            <Box>
                              <p>{item.text}</p>
                              <button
                                onClick={() => startEditing(item.id, item.text)}
                              >
                                <Edit2 />
                                Edit
                              </button>
                            </Box>
                          )}
                        </Box>
                      </Box>
                    </Box>
                  ))}
                </Box>
              </Box>
            )}
          </Box>
        </Box>

        {/* Image Upload - Full Width - only show after refine context */}
        {/* {result && result.context && <ImageUpload />} */}

        {/* Image Comparison Results - Full Width Below */}
        {/* {comparisonResults && comparisonResults.success && (
          <ComparisonResults />
        )} */}

        {/* Final Review Section */}
        {/* {finalReview && <FinalReview />} */}
      </Box>
    </Box>
  );
}

type AppProps = {
  mode: ThemeMode;
  toggleTheme: () => void;
};

export default function App({ mode, toggleTheme }: AppProps) {
  return (
    <Box
      sx={{
        minHeight: "100vh",
        bgcolor: "background.default",
        p: 2,
      }}
    >
      {/* Navigation Links */}
      <Box sx={{ mb: 4, display: "flex", gap: 2 }}>
        <Link to="/">Home</Link>
        <Link to="/settings">Settings</Link>
      </Box>

      <Routes>
        <Route
          path="/"
          element={
            <Box textAlign="center">
              <Typography variant="h4" gutterBottom>
                Home Page
              </Typography>
              <Typography>Current theme: {mode}</Typography>
            </Box>
          }
        />
        <Route
          path="/settings"
          element={<Settings mode={mode} toggleTheme={toggleTheme} />}
        />
      </Routes>
    </Box>
  );
}
