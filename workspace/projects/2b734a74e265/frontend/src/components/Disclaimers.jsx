import React from 'react';
import { AlertTriangle, Database, Info, ShieldAlert, Activity } from 'lucide-react';

export default function Disclaimers({ metadata }) {
  if (!metadata) return null;

  return (
    <div className="disclaimers-container" data-testid="disclaimers-section">
      
      {metadata.is_curated_fallback && (
        <div className="warning-banner" data-testid="fallback-warning">
          <AlertTriangle size={20} className="warning-icon" />
          <div className="warning-content">
            <strong>Curated Fallback Data Active</strong>
            <p>Live search returned insufficient results. Displaying curated fallback data for demonstration purposes.</p>
          </div>
        </div>
      )}

      <div className="metadata-grid">
        <div className="metadata-card" data-testid="meta-universe">
          <Database size={18} className="text-muted" />
          <div className="meta-info">
            <span className="meta-label">Universe Size</span>
            <span className="meta-value">{metadata.universe_size?.toLocaleString() || 'N/A'}</span>
          </div>
        </div>
        
        <div className="metadata-card" data-testid="meta-scanned">
          <Activity size={18} className="text-muted" />
          <div className="meta-info">
            <span className="meta-label">Scanned Count</span>
            <span className="meta-value">{metadata.scanned_count?.toLocaleString() || 'N/A'}</span>
          </div>
        </div>
        
        <div className="metadata-card" data-testid="meta-valid">
          <Database size={18} className="text-muted" />
          <div className="meta-info">
            <span className="meta-label">Valid Calls</span>
            <span className="meta-value">{metadata.valid_calls?.toLocaleString() || 'N/A'}</span>
          </div>
        </div>
        
        <div className="metadata-card" data-testid="meta-source">
          <Info size={18} className="text-muted" />
          <div className="meta-info">
            <span className="meta-label">Source Status</span>
            <span className="meta-value">{metadata.source_status || 'Unknown'}</span>
          </div>
        </div>
      </div>

      {metadata.limitations && (
        <div className="limitations-box" data-testid="meta-limitations">
          <h4 className="limitations-title">Data Limitations</h4>
          <p className="limitations-text">{metadata.limitations}</p>
        </div>
      )}

      <div className="legal-disclaimer" data-testid="legal-disclaimer">
        <ShieldAlert size={18} className="legal-icon" />
        <div className="legal-content">
          <strong>Not Financial Advice</strong>
          <p>
            The information provided by this application is for informational and educational purposes only. 
            It does not constitute financial, investment, or trading advice. Analyst scores and solvency metrics 
            are aggregated from third-party sources and may be delayed or inaccurate. Always conduct your own 
            due diligence and consult with a licensed financial advisor before making any investment decisions.
          </p>
        </div>
      </div>
    </div>
  );
}