import React, { useState } from 'react';
import { ChevronDown, ChevronRight, ExternalLink, FileText } from 'lucide-react';
import './Sources.css';

const Sources = ({ sources = [] }) => {
  const [expandedSources, setExpandedSources] = useState(new Set());

  if (!sources || sources.length === 0) {
    return null;
  }

  const toggleSource = (index) => {
    const newExpanded = new Set(expandedSources);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedSources(newExpanded);
  };

  const formatSourceName = (source) => {
    if (!source.title && !source.source) return `Source ${source.index || 1}`;
    
    // Use title if available, otherwise use source
    let name = source.title || source.source || '';
    
    // Clean up source names
    if (name.startsWith('PDF_')) {
      name = name.substring(4);
    }
    if (name.endsWith('.txt')) {
      name = name.substring(0, name.length - 4);
    }
    
    // Format common patterns
    name = name
      .replace(/-/g, ' ')
      .replace(/_/g, ' ')
      .replace(/([A-Z])/g, ' $1')
      .trim()
      .replace(/\s+/g, ' ');
    
    // Capitalize first letter of each word
    return name.split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ');
  };

  const getSourceType = (source) => {
    if (!source.title && !source.source) return 'document';
    
    const name = (source.title || source.source || '').toLowerCase();
    if (name.includes('pdf')) return 'pdf';
    if (name.includes('policy') || name.includes('terms')) return 'policy';
    if (name.includes('disclosure')) return 'disclosure';
    if (name.includes('booklet')) return 'guide';
    return 'document';
  };

  const getSourceIcon = (type) => {
    switch (type) {
      case 'pdf': return <FileText size={14} className="source-icon pdf" />;
      case 'policy': return <FileText size={14} className="source-icon policy" />;
      case 'disclosure': return <FileText size={14} className="source-icon disclosure" />;
      case 'guide': return <FileText size={14} className="source-icon guide" />;
      default: return <FileText size={14} className="source-icon document" />;
    }
  };

  return (
    <div className="sources-container">
      <div className="sources-header">
        <span className="sources-title">Sources</span>
        <span className="sources-count">{sources.length}</span>
      </div>
      
      <div className="sources-list">
        {sources.map((source, index) => {
          const isExpanded = expandedSources.has(index);
          const sourceType = getSourceType(source);
          const sourceName = formatSourceName(source);
          
          return (
            <div key={index} className={`source-item ${isExpanded ? 'expanded' : ''}`}>
              <div 
                className="source-header" 
                onClick={() => toggleSource(index)}
                role="button"
                tabIndex={0}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    toggleSource(index);
                  }
                }}
              >
                <div className="source-main-info">
                  <div className="source-toggle">
                    {isExpanded ? (
                      <ChevronDown size={16} />
                    ) : (
                      <ChevronRight size={16} />
                    )}
                  </div>
                  
                  <div className="source-details">
                    <div className="source-name-row">
                      {getSourceIcon(sourceType)}
                      <span className="source-name">{sourceName}</span>
                      {source.source_reference && (
                        <a 
                          href={source.source_reference} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="source-link"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <ExternalLink size={14} />
                        </a>
                      )}
                    </div>
                    
                    {/* Remove confidence display since API doesn't return scores */}
                  </div>
                </div>
              </div>
              
              {isExpanded && (
                <div className="source-content">
                  <div className="source-metadata">
                    <div className="metadata-row">
                      <span className="metadata-label">Document Type:</span>
                      <span className="metadata-value">{sourceType.charAt(0).toUpperCase() + sourceType.slice(1)}</span>
                    </div>
                    
                    {source.source_reference && (
                      <div className="metadata-row">
                        <span className="metadata-label">Source URL:</span>
                        <span className="metadata-value">
                          <a 
                            href={source.source_reference} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="metadata-link"
                          >
                            {source.source_reference}
                          </a>
                        </span>
                      </div>
                    )}
                    
                    {source.title && (
                      <div className="metadata-row">
                        <span className="metadata-label">Title:</span>
                        <span className="metadata-value">{source.title}</span>
                      </div>
                    )}
                    
                    {source.source && (
                      <div className="metadata-row">
                        <span className="metadata-label">File Name:</span>
                        <span className="metadata-value">{source.source}</span>
                      </div>
                    )}
                    
                    {source.id && (
                      <div className="metadata-row">
                        <span className="metadata-label">Document ID:</span>
                        <span className="metadata-value font-mono">{source.id}</span>
                      </div>
                    )}
                  </div>
                  
                  {source.metadata && source.metadata.content && (
                    <div className="source-preview">
                      <div className="preview-label">Content Preview:</div>
                      <div className="preview-content">
                        {source.metadata.content.substring(0, 200)}
                        {source.metadata.content.length > 200 && '...'}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default Sources;
