right-2 bg-red-500 hover:bg-red-600 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Submit Button */}
            <button
              onClick={handleSubmit}
              disabled={!draft || !apiKey || loading}
              className="w-full bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white font-semibold py-3 px-6 rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Target className="w-5 h-5" />
                  Analyze Draft
                </>
              )}
            </button>
          </div>

          {/* Right Column - Results */}
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
                      Feedback Items
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
                    onClick={exportCheckedItems}
                    disabled={checkedCount === 0}
                    className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200 disabled:bg-gray-100 disabled:text-gray-400 flex items-center gap-1"
                  >
                    <Download className="w-4 h-4" />
                    Export Selected
                  </button>
                </div>

                {/* Items List */}
                <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2">
                  {result.items.map((item) => (
                    <div
                      key={item.id}
                      className={`border rounded-lg p-4 transition-all ${
                        checkedItems[item.id]
                          ? 'bg-purple-50 border-purple-300'
                          : 'bg-white border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <input
                          type="checkbox"
                          checked={checkedItems[item.id] || false}
                          onChange={() => toggleItem(item.id)}
                          className="mt-1 w-5 h-5 text-purple-600 rounded focus:ring-2 focus:ring-purple-500"
                        />
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                          </div>
                          <h3 className="font-semibold text-gray-900 mb-1">
                            {item.text}
                          </h3>
                          <p className="text-sm text-gray-700 whitespace-pre-wrap">
                            {item.details}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {result.usage && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <p className="text-xs text-gray-500">
                      Model: {result.model} |
                      Input: {result.usage.input_tokens.toLocaleString()} tokens |
                      Output: {result.usage.output_tokens.toLocaleString()} tokens
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}