import React, { useState } from 'react';
import { FileText, Target, Upload, X, CheckCircle, AlertCircle, Filter, Edit2, Save, XCircle, Image as ImageIcon } from 'lucide-react';

export default function PaperEditor() {
  const [draft, setDraft] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [images, setImages] = useState([]);
  const [error, setError] = useState(null);
  const [checkedItems, setCheckedItems] = useState({});
  const [editingItems, setEditingItems] = useState({});
  const [editedTexts, setEditedTexts] = useState({});
  const [comparisonResults, setComparisonResults] = useState(null);

  const handleImageUpload = async (e) => {
    const files = Array.from(e.target.files);

    // Convert images to base64
    const imagePromises = files.map(file => {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
          resolve({
            name: file.name,
            type: file.type,
            data: reader.result.split(',')[1],
            preview: reader.result
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
      console.error('Error loading images:', error);
      setError('Failed to load images. Please try again.');
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
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          apiKey: apiKey,
          draft: draft
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || `Server error: ${response.status}`);
      }

      setResult(data);
      // Initialize all items as checked
      const initialChecked = {};
      if (data.items) {
        data.items.forEach(item => {
          initialChecked[item.id] = true;
        });
      }
      setCheckedItems(initialChecked);
    } catch (err) {
      setError(err.message);
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleItem = (itemId) => {
    setCheckedItems(prev => ({
      ...prev,
      [itemId]: !prev[itemId]
    }));
  };

  const toggleAll = (checked) => {
    const newChecked = {};
    if (result?.items) {
      result.items.forEach(item => {
        newChecked[item.id] = checked;
      });
    }
    setCheckedItems(newChecked);
  };

  const startEditing = (itemId, currentText) => {
    setEditingItems(prev => ({ ...prev, [itemId]: true }));
    setEditedTexts(prev => ({ ...prev, [itemId]: currentText }));
  };

  const cancelEditing = (itemId) => {
    setEditingItems(prev => ({ ...prev, [itemId]: false }));
    setEditedTexts(prev => {
      const newTexts = { ...prev };
      delete newTexts[itemId];
      return newTexts;
    });
  };

  const saveEdit = (itemId) => {
    if (!result?.items) return;

    const updatedItems = result.items.map(item =>
      item.id === itemId ? { ...item, text: editedTexts[itemId] } : item
    );

    setResult({ ...result, items: updatedItems });
    setEditingItems(prev => ({ ...prev, [itemId]: false }));
  };

  const refineContext = async () => {
    if (!result?.items) return;

    const checkedItemsList = result.items.filter(item => checkedItems[item.id]);

    if (checkedItemsList.length === 0) {
      setError('Please select at least one item to send');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch("http://localhost:5001/api/refine_context", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          apiKey: apiKey,
          selectedItems: checkedItemsList,
          draft: draft
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || `Server error: ${response.status}`);
      }

      // Handle the response from the agent
      console.log('Agent response:', data);

      // Update result with the refined context
      setResult(prev => ({
        ...prev,
        context: data.context
      }));

    } catch (err) {
      setError(err.message);
      console.error('Error sending to agent:', err);
    } finally {
      setLoading(false);
    }
  };

  const analyzeImages = async () => {
    if (images.length === 0) return;

    // Check if we have refined context available
    if (!result?.context) {
      setError('Please refine context before analyzing images');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch("http://localhost:5001/api/analyze_images", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          apiKey: apiKey,
          draft: draft,
          context: result.context,
          images: images.map(img => ({
            type: img.type,
            data: img.data,
            name: img.name
          }))
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || `Server error: ${response.status}`);
      }

      console.log('Image analysis response:', data);

      // Store the comparison results
      setComparisonResults(data);

    } catch (err) {
      setError(err.message);
      console.error('Error analyzing images:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-2 flex items-center justify-center gap-3">
            <FileText className="w-10 h-10 text-purple-600" />
            Paper Review Assistant
          </h1>
          <p className="text-gray-600">Analyze your paper draft with AI-powered insights</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Left Column - Input */}
          <div className="space-y-6">
            {/* API Key Input */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Anthropic API Key
              </label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="sk-ant-..."
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>

            {/* Draft Text Input */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Paper Draft
              </label>
              <textarea
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                placeholder="Paste your paper draft here..."
                rows={8}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
              />
            </div>

            {/* Create Context Button */}
            <button
              onClick={createContext}
              disabled={!draft || !apiKey || loading}
              className="w-full bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white font-semibold py-3 px-6 rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Creating Context...
                </>
              ) : (
                <>
                  <Target className="w-5 h-5" />
                  Create Context
                </>
              )}
            </button>

            {/* Image Upload - only show after refine context */}
            {result && result.context && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Upload Images (Optional)
              </label>

              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-purple-500 transition-colors">
                <input
                  type="file"
                  id="image-upload"
                  accept="image/*"
                  multiple
                  onChange={handleImageUpload}
                  className="hidden"
                />
                <label
                  htmlFor="image-upload"
                  className="cursor-pointer flex flex-col items-center gap-2"
                >
                  <Upload className="w-8 h-8 text-gray-400" />
                  <span className="text-sm text-gray-600">
                    Click to upload images
                  </span>
                </label>
              </div>

              {images.length > 0 && (
                <div className="mt-4 grid grid-cols-2 gap-4">
                  {images.map((image, index) => (
                    <div key={index} className="relative group">
                      <img
                        src={image.preview}
                        alt={image.name}
                        className="w-full h-32 object-cover rounded-lg border border-gray-200"
                      />
                      <button
                        onClick={() => removeImage(index)}
                        className="absolute top-2 right-2 bg-red-500 hover:bg-red-600 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          <X className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Analyze Images Button */}
              {images.length > 0 && (
                <button
                  onClick={analyzeImages}
                  disabled={loading}
                  className="w-full mt-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-3 px-6 rounded-lg transition-colors flex items-center justify-center gap-2"
                >
                  {loading ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      Analyzing Images...
                    </>
                  ) : (
                    <>
                      <Target className="w-5 h-5" />
                      Analyze Images
                    </>
                  )}
                </button>
              )}
            </div>
            )}
          </div>

          {/* Right Column - Context Results (Compact) */}
          <div className="space-y-6">
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="font-semibold text-red-900">Error</h3>
                  <p className="text-sm text-red-700 mt-1">{error}</p>
                </div>
              </div>
            )}

            {result && result.success && result.items && (
              <div className="bg-white rounded-lg shadow-lg p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-6 h-6 text-green-600" />
                    <h2 className="text-xl font-bold text-gray-900">
                      Context
                    </h2>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-600">
                      {Object.values(checkedItems).filter(Boolean).length} of {result.items.length} selected
                    </span>
                  </div>
                </div>

                {/* Controls */}
                <div className="flex flex-wrap gap-2 mb-4 pb-4 border-b border-gray-200">
                  <button
                    onClick={() => toggleAll(true)}
                    className="px-3 py-1 text-sm bg-purple-100 text-purple-700 rounded hover:bg-purple-200"
                  >
                    Select All
                  </button>
                  <button
                    onClick={() => toggleAll(false)}
                    className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                  >
                    Deselect All
                  </button>
                  <button
                    onClick={refineContext}
                    disabled={Object.values(checkedItems).filter(Boolean).length === 0 || loading}
                    className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200 disabled:bg-gray-100 disabled:text-gray-400 flex items-center gap-1"
                  >
                    <Target className="w-4 h-4" />
                    Refine Context
                  </button>
                </div>

                {/* Items List - COMPACT VERSION */}
                <div className="space-y-2 max-h-[300px] overflow-y-auto pr-2">
                  {result.items.map((item) => (
                    <div
                      key={item.id}
                      className={`border rounded p-3 transition-all ${
                        checkedItems[item.id]
                          ? 'bg-purple-50 border-purple-300'
                          : 'bg-white border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className="flex items-start gap-2">
                        <input
                          type="checkbox"
                          checked={checkedItems[item.id] || false}
                          onChange={() => toggleItem(item.id)}
                          className="mt-0.5 w-4 h-4 text-purple-600 rounded focus:ring-2 focus:ring-purple-500"
                        />
                        <div className="flex-1 min-w-0">
                          {editingItems[item.id] ? (
                            <div className="space-y-2">
                              <textarea
                                value={editedTexts[item.id] || item.text}
                                onChange={(e) => setEditedTexts(prev => ({
                                  ...prev,
                                  [item.id]: e.target.value
                                }))}
                                className="w-full p-2 border border-gray-300 rounded text-xs focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
                                rows={3}
                              />
                              <div className="flex gap-2">
                                <button
                                  onClick={() => saveEdit(item.id)}
                                  className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded hover:bg-green-200 flex items-center gap-1"
                                >
                                  <Save className="w-3 h-3" />
                                  Save
                                </button>
                                <button
                                  onClick={() => cancelEditing(item.id)}
                                  className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200 flex items-center gap-1"
                                >
                                  <XCircle className="w-3 h-3" />
                                  Cancel
                                </button>
                              </div>
                            </div>
                          ) : (
                            <div>
                              <p className="text-xs text-gray-700 whitespace-pre-wrap line-clamp-3">
                                {item.text}
                              </p>
                              <button
                                onClick={() => startEditing(item.id, item.text)}
                                className="mt-1 px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 flex items-center gap-1"
                              >
                                <Edit2 className="w-3 h-3" />
                                Edit
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Image Comparison Results - Full Width Below */}
        {comparisonResults && comparisonResults.success && (
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center gap-2 mb-6">
              <ImageIcon className="w-6 h-6 text-blue-600" />
              <h2 className="text-2xl font-bold text-gray-900">
                Figure Analysis
              </h2>
            </div>

            <div className="space-y-8">
              {images.map((originalImage, index) => {
                const expectedImageData = comparisonResults.expected_images?.[index];
                const mediaType = comparisonResults.expected_media_types?.[index];
                const similarities = comparisonResults.figure_similarities?.[index];
                const differences = comparisonResults.figure_differences?.[index];

                return (
                  <div key={index} className="border border-gray-200 rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                      {originalImage.name}
                    </h3>

                    {/* Side-by-side images */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                      {/* Original Image */}
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-2">
                          Original Figure
                        </h4>
                        <div className="border border-gray-300 rounded-lg overflow-hidden bg-gray-50">
                          <img
                            src={originalImage.preview}
                            alt={`Original ${originalImage.name}`}
                            className="w-full h-auto"
                          />
                        </div>
                      </div>

                      {/* Expected Image */}
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-2">
                          Expected Figure (Generated)
                        </h4>
                        <div className="border border-gray-300 rounded-lg overflow-hidden bg-gray-50">
                          {expectedImageData && mediaType ? (
                            <img
                              src={`data:${mediaType};base64,${expectedImageData}`}
                              alt={`Expected ${originalImage.name}`}
                              className="w-full h-auto"
                            />
                          ) : (
                            <div className="w-full h-64 flex items-center justify-center text-gray-400">
                              No expected image generated
                            </div>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Similarities and Differences */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {/* Similarities */}
                      <div>
                        <h4 className="text-sm font-semibold text-green-700 mb-2 flex items-center gap-2">
                          <CheckCircle className="w-4 h-4" />
                          Similarities
                        </h4>
                        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                          <p className="text-sm text-gray-700 whitespace-pre-wrap">
                            {similarities || 'No similarities analysis available'}
                          </p>
                        </div>
                      </div>

                      {/* Differences */}
                      <div>
                        <h4 className="text-sm font-semibold text-orange-700 mb-2 flex items-center gap-2">
                          <AlertCircle className="w-4 h-4" />
                          Differences
                        </h4>
                        <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                          <p className="text-sm text-gray-700 whitespace-pre-wrap">
                            {differences || 'No differences analysis available'}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

      </div>
    </div>
  );
}