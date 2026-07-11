import { useState, useEffect } from 'react';
import { exceptionsApi, dashboardApi } from './api';
import { AlertCircle, CheckCircle, Clock, TrendingDown, Filter, X } from 'lucide-react';
import './App.css';

function App() {
  const [view, setView] = useState('dashboard');
  const [exceptions, setExceptions] = useState([]);
  const [selectedException, setSelectedException] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [filters, setFilters] = useState({
    severity: '',
    status: '',
    product_code: '',
    plant_id: '',
  });
  const [pagination, setPagination] = useState({
    page: 1,
    page_size: 20,
    total: 0,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  useEffect(() => {
    if (view === 'exceptions') {
      loadExceptions();
    }
  }, [view, filters, pagination.page]);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const data = await dashboardApi.getSummary();
      setDashboard(data);
    } catch (err) {
      setError('Failed to load dashboard data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadExceptions = async () => {
    try {
      setLoading(true);
      setError(null);
      const params = Object.fromEntries(Object.entries({
        ...filters,
        page: pagination.page,
        page_size: pagination.page_size,
      }).filter(([, value]) => value !== '' && value !== null && value !== undefined));
      const data = await exceptionsApi.getExceptions(params);
      setExceptions(data.items);
      setPagination(prev => ({ ...prev, total: data.total }));
    } catch (err) {
      setError('Failed to load exceptions');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadExceptionDetail = async (id) => {
    try {
      setLoading(true);
      const data = await exceptionsApi.getExceptionDetail(id);
      setSelectedException(data);
    } catch (err) {
      setError('Failed to load exception details');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const updateStatus = async (id, newStatus) => {
    try {
      await exceptionsApi.updateExceptionStatus(id, newStatus);
      if (selectedException && selectedException.id === id) {
        setSelectedException(prev => ({ ...prev, status: newStatus }));
      }
      loadExceptions();
      loadDashboard();
    } catch (err) {
      setError('Failed to update status');
      console.error(err);
    }
  };

  const clearFilters = () => {
    setFilters({ severity: '', status: '', product_code: '', plant_id: '' });
    setPagination(prev => ({ ...prev, page: 1 }));
  };

  const getSeverityColor = (severity) => {
    return severity === 'high' ? 'text-red-600 bg-red-50' : 'text-yellow-600 bg-yellow-50';
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'open': return 'text-red-600 bg-red-50';
      case 'acknowledged': return 'text-yellow-600 bg-yellow-50';
      case 'resolved': return 'text-green-600 bg-green-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  if (loading && !dashboard) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-600">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <button
                onClick={() => setView('dashboard')}
                className={`px-4 py-2 text-sm font-medium ${
                  view === 'dashboard' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'
                }`}
              >
                Dashboard
              </button>
              <button
                onClick={() => setView('exceptions')}
                className={`px-4 py-2 text-sm font-medium ${
                  view === 'exceptions' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'
                }`}
              >
                Exceptions
              </button>
            </div>
          </div>
        </div>
      </nav>

      {error && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4">
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        </div>
      )}

      {view === 'dashboard' && dashboard && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-6">Production Exception Dashboard</h1>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <AlertCircle className="h-8 w-8 text-red-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Total Exceptions</p>
                  <p className="text-2xl font-semibold text-gray-900">{dashboard.total_exceptions}</p>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <Clock className="h-8 w-8 text-yellow-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Open</p>
                  <p className="text-2xl font-semibold text-gray-900">{dashboard.open_count}</p>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <CheckCircle className="h-8 w-8 text-green-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Resolved</p>
                  <p className="text-2xl font-semibold text-gray-900">{dashboard.resolved_count}</p>
                </div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Severity Distribution</h2>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">High Severity</span>
                  <span className="px-2 py-1 text-xs font-medium bg-red-100 text-red-800 rounded">
                    {dashboard.high_severity_count}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Medium Severity</span>
                  <span className="px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 rounded">
                    {dashboard.medium_severity_count}
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Top Products</h2>
              <div className="space-y-2">
                {dashboard.exceptions_by_product.slice(0, 5).map((item, idx) => (
                  <div key={idx} className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">{item.product_code}</span>
                    <span className="text-sm font-medium text-gray-900">{item.count}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {view === 'exceptions' && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-3xl font-bold text-gray-900">Exceptions</h1>
            <button
              onClick={() => setView('dashboard')}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              Back to Dashboard
            </button>
          </div>

          <div className="bg-white rounded-lg shadow mb-6 p-4">
            <div className="flex items-center mb-4">
              <Filter className="h-5 w-5 text-gray-500 mr-2" />
              <h3 className="text-sm font-medium text-gray-700">Filters</h3>
              <button
                onClick={clearFilters}
                className="ml-auto text-sm text-blue-600 hover:text-blue-800"
              >
                Clear
              </button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <select
                value={filters.severity}
                onChange={(e) => setFilters({ ...filters, severity: e.target.value })}
                className="border border-gray-300 rounded-md px-3 py-2 text-sm"
              >
                <option value="">All Severities</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
              </select>
              <select
                value={filters.status}
                onChange={(e) => setFilters({ ...filters, status: e.target.value })}
                className="border border-gray-300 rounded-md px-3 py-2 text-sm"
              >
                <option value="">All Statuses</option>
                <option value="open">Open</option>
                <option value="acknowledged">Acknowledged</option>
                <option value="resolved">Resolved</option>
              </select>
              <input
                type="text"
                placeholder="Product Code"
                value={filters.product_code}
                onChange={(e) => setFilters({ ...filters, product_code: e.target.value })}
                className="border border-gray-300 rounded-md px-3 py-2 text-sm"
              />
              <input
                type="text"
                placeholder="Plant ID"
                value={filters.plant_id}
                onChange={(e) => setFilters({ ...filters, plant_id: e.target.value })}
                className="border border-gray-300 rounded-md px-3 py-2 text-sm"
              />
            </div>
          </div>

          {loading ? (
            <div className="text-center py-8 text-gray-600">Loading exceptions...</div>
          ) : (
            <>
              <div className="bg-white rounded-lg shadow overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Product</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Plant</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Ratio</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Severity</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {exceptions.map((exc) => (
                      <tr key={exc.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {new Date(exc.date).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {exc.product_code}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {exc.plant_id}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {(exc.production_ratio * 100).toFixed(1)}%
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 text-xs font-medium rounded ${getSeverityColor(exc.severity)}`}>
                            {exc.severity.toUpperCase()}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 text-xs font-medium rounded ${getStatusColor(exc.status)}`}>
                            {exc.status.toUpperCase()}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <button
                            onClick={() => loadExceptionDetail(exc.id)}
                            className="text-blue-600 hover:text-blue-900 mr-3"
                          >
                            View
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="mt-4 flex justify-between items-center">
                <div className="text-sm text-gray-600">
                  Showing {((pagination.page - 1) * pagination.page_size) + 1} to {Math.min(pagination.page * pagination.page_size, pagination.total)} of {pagination.total}
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => setPagination(prev => ({ ...prev, page: Math.max(1, prev.page - 1) }))}
                    disabled={pagination.page === 1}
                    className="px-3 py-1 border rounded text-sm disabled:opacity-50"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
                    disabled={pagination.page * pagination.page_size >= pagination.total}
                    className="px-3 py-1 border rounded text-sm disabled:opacity-50"
                  >
                    Next
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {selectedException && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-start mb-4">
                <h2 className="text-xl font-bold text-gray-900">Exception Details</h2>
                <button
                  onClick={() => setSelectedException(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>

              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm font-medium text-gray-500">Product Code</p>
                    <p className="text-lg font-semibold text-gray-900">{selectedException.product_code}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-500">Plant ID</p>
                    <p className="text-lg font-semibold text-gray-900">{selectedException.plant_id}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-500">Date</p>
                    <p className="text-lg font-semibold text-gray-900">{new Date(selectedException.date).toLocaleDateString()}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-500">Production Ratio</p>
                    <p className="text-lg font-semibold text-gray-900">{(selectedException.production_ratio * 100).toFixed(1)}%</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-500">Planned Units</p>
                    <p className="text-lg font-semibold text-gray-900">{selectedException.planned_units}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-500">Units Produced</p>
                    <p className="text-lg font-semibold text-gray-900">{selectedException.units_produced}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-500">Deficit Units</p>
                    <p className="text-lg font-semibold text-red-600">{selectedException.deficit_units}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-500">Severity</p>
                    <span className={`px-2 py-1 text-xs font-medium rounded ${getSeverityColor(selectedException.severity)}`}>
                      {selectedException.severity.toUpperCase()}
                    </span>
                  </div>
                </div>

                <div>
                  <p className="text-sm font-medium text-gray-500 mb-2">Status</p>
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 text-xs font-medium rounded ${getStatusColor(selectedException.status)}`}>
                      {selectedException.status.toUpperCase()}
                    </span>
                    {selectedException.status !== 'resolved' && (
                      <button
                        onClick={() => {
                          const nextStatus = selectedException.status === 'open' ? 'acknowledged' : 'resolved';
                          updateStatus(selectedException.id, nextStatus);
                        }}
                        className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
                      >
                        {selectedException.status === 'open' ? 'Acknowledge' : 'Resolve'}
                      </button>
                    )}
                  </div>
                </div>

                {selectedException.trend && selectedException.trend.length > 0 && (
                  <div>
                    <p className="text-sm font-medium text-gray-500 mb-2">7-Day Trend</p>
                    <div className="h-32 flex items-end space-x-1">
                      {selectedException.trend.map((point, idx) => (
                        <div
                          key={idx}
                          className="flex-1 bg-blue-200 hover:bg-blue-300 transition-colors relative"
                          style={{ height: `${Math.min(point.production_ratio * 100, 100)}%` }}
                          title={`${new Date(point.date).toLocaleDateString()}: ${(point.production_ratio * 100).toFixed(1)}%`}
                        >
                          <div className="absolute bottom-0 left-0 right-0 text-xs text-center text-gray-600 pb-1">
                            {(point.production_ratio * 100).toFixed(0)}%
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
