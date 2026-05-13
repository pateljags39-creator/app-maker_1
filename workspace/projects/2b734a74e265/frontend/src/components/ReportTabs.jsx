import React, { useState } from 'react';
import { User, List, BarChart2, ShieldCheck, AlertCircle } from 'lucide-react';

export default function ReportTabs({ data }) {
  const [activeTab, setActiveTab] = useState('analyst');

  if (!data) {
    return null;
  }

  const { analyst, recommendations, company_metrics, metadata } = data;

  const tabs = [
    { id: 'analyst', label: 'Analyst Summary', icon: User },
    { id: 'watchlist', label: 'Watchlist', icon: List },
    { id: 'matrix', label: 'Comparison Matrix', icon: BarChart2 },
    { id: 'integrity', label: 'Data Integrity', icon: ShieldCheck },
  ];

  return (
    <div className="report-tabs-container" data-testid="report-tabs">
      <div className="tabs-header" role="tablist">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              role="tab"
              aria-selected={activeTab === tab.id}
              className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
              data-testid={`tab-${tab.id}`}
            >
              <Icon size={18} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      <div className="tab-content-area">
        {activeTab === 'analyst' && (
          <div className="card fade-in" data-testid="tab-content-analyst">
            <h3 className="card-title">Analyst Profile</h3>
            {analyst ? (
              <div className="profile-grid">
                <div className="profile-item">
                  <span className="label">Name</span>
                  <span className="value">{analyst.name}</span>
                </div>
                <div className="profile-item">
                  <span className="label">Firm</span>
                  <span className="value">{analyst.firm}</span>
                </div>
                <div className="profile-item">
                  <span className="label">Credibility Score</span>
                  <span className="value highlight">
                    {analyst.score} <span className="text-muted">({analyst.score_type})</span>
                  </span>
                </div>
              </div>
            ) : (
              <p className="empty-state">No analyst data available.</p>
            )}
          </div>
        )}

        {activeTab === 'watchlist' && (
          <div className="card fade-in" data-testid="tab-content-watchlist">
            <h3 className="card-title">Recommended Assets</h3>
            {recommendations && recommendations.length > 0 ? (
              <div className="table-responsive">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Ticker</th>
                      <th>Asset Type</th>
                      <th>Call Type</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recommendations.map((rec) => (
                      <tr key={rec.id || rec.ticker}>
                        <td><strong>{rec.ticker}</strong></td>
                        <td>{rec.asset_type}</td>
                        <td>
                          <span className={`badge badge-${rec.call_type?.toLowerCase()}`}>
                            {rec.call_type}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="empty-state">
                <p>No recommendations found for this filter criteria.</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'matrix' && (
          <div className="card fade-in" data-testid="tab-content-matrix">
            <h3 className="card-title">Company Solvency Metrics</h3>
            {company_metrics && company_metrics.length > 0 ? (
              <div className="table-responsive">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Ticker</th>
                      <th>Solvency Score</th>
                      <th>Debt to Equity</th>
                      <th>Current Ratio</th>
                      <th>Free Cash Flow</th>
                    </tr>
                  </thead>
                  <tbody>
                    {company_metrics.map((metric) => (
                      <tr key={metric.id || metric.ticker}>
                        <td><strong>{metric.ticker}</strong></td>
                        <td>{metric.solvency_score?.toFixed(2)}</td>
                        <td>{metric.debt_to_equity?.toFixed(2)}</td>
                        <td>{metric.current_ratio?.toFixed(2)}</td>
                        <td>
                          {metric.free_cash_flow != null 
                            ? `$${Number(metric.free_cash_flow).toLocaleString()}` 
                            : 'N/A'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="empty-state">
                <p>No solvency metrics available for the current watchlist.</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'integrity' && (
          <div className="card fade-in" data-testid="tab-content-integrity">
            <h3 className="card-title">Report Metadata & Integrity</h3>
            {metadata ? (
              <div className="metadata-container">
                {metadata.is_curated_fallback && (
                  <div className="alert alert-warning" data-testid="fallback-warning">
                    <AlertCircle size={18} />
                    <span><strong>Notice:</strong> Displaying curated fallback data due to live source limitations.</span>
                  </div>
                )}
                
                <div className="profile-grid">
                  <div className="profile-item">
                    <span className="label">Universe Size</span>
                    <span className="value">{metadata.universe_size}</span>
                  </div>
                  <div className="profile-item">
                    <span className="label">Scanned Count</span>
                    <span className="value">{metadata.scanned_count}</span>
                  </div>
                  <div className="profile-item">
                    <span className="label">Valid Calls</span>
                    <span className="value">{metadata.valid_calls}</span>
                  </div>
                  <div className="profile-item">
                    <span className="label">Source Status</span>
                    <span className="value">{metadata.source_status}</span>
                  </div>
                </div>

                {metadata.limitations && (
                  <div className="limitations-box">
                    <h4 className="label">Known Limitations</h4>
                    <p className="text-muted">{metadata.limitations}</p>
                  </div>
                )}
              </div>
            ) : (
              <p className="empty-state">No metadata available.</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}