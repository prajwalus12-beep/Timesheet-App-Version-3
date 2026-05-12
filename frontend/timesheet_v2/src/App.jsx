import React, { useState, useEffect } from "react"
import { 
  Clock, 
  FileText, 
  Edit3, 
  Trash2, 
  Copy, 
  MoreHorizontal, 
  ChevronLeft, 
  ChevronRight,
  Search,
  Plus,
  Filter,
  MessageSquare,
  Activity,
  Calendar,
  User,
  ExternalLink,
  CheckCircle2,
  AlertCircle
} from "lucide-react"
import { Streamlit } from "streamlit-component-lib"

const TimesheetTable = ({ data, startOfWeek, endOfWeek, isReadOnly }) => {
  const [searchTerm, setSearchTerm] = useState("")
  
  const phaseLabels = {
    "1": "Analysis",
    "2": "Design",
    "3": "Development",
    "4": "Testing",
    "5": "Deployment",
    "6": "Support"
  }

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'complete': return 'bg-emerald-50 text-emerald-700 border-emerald-100'
      case 'in progress': return 'bg-blue-50 text-blue-700 border-blue-100'
      case 'in testing': return 'bg-amber-50 text-amber-700 border-amber-100'
      case 'on hold': return 'bg-slate-50 text-slate-600 border-slate-100'
      default: return 'bg-slate-50 text-slate-600 border-slate-100'
    }
  }

  const handleAction = (action, rowId) => {
    Streamlit.setComponentValue({ action, rowId })
  }

  const filteredData = data.filter(row => 
    row.project_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    row.emp_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    row.comment?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  useEffect(() => {
    Streamlit.setFrameHeight()
  }, [filteredData])

  return (
    <div className="w-full bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
      {/* Header / Toolbar */}
      <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input 
              type="text" 
              placeholder="Filter activities..." 
              className="pl-9 pr-4 py-1.5 bg-white border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 w-64 transition-all"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <button className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-slate-600 hover:bg-white hover:shadow-sm border border-transparent hover:border-slate-200 rounded-lg transition-all">
            <Filter className="h-4 w-4" />
            Advanced
          </button>
        </div>
        
        <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">
          {filteredData.length} records found
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-left">
          <thead>
            <tr className="border-b border-slate-100 bg-slate-50/30">
              <th className="pl-6 py-3 text-[11px] font-semibold text-slate-500 uppercase tracking-widest w-32">Date</th>
              <th className="px-4 py-3 text-[11px] font-semibold text-slate-500 uppercase tracking-widest">Activity & Project</th>
              <th className="px-4 py-3 text-[11px] font-semibold text-slate-500 uppercase tracking-widest w-48">Resource</th>
              <th className="px-4 py-3 text-[11px] font-semibold text-slate-500 uppercase tracking-widest w-40 text-center">Status</th>
              <th className="px-4 py-3 text-[11px] font-semibold text-slate-500 uppercase tracking-widest w-24 text-right">Time</th>
              <th className="pr-6 py-3 text-[11px] font-semibold text-slate-500 uppercase tracking-widest w-28 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {filteredData.map((row) => {
              const rowDate = new Date(row.date)
              const isEditable = !isReadOnly && rowDate >= new Date(startOfWeek) && rowDate <= new Date(endOfWeek)
              
              return (
                <tr key={row.id} className="group hover:bg-slate-50/80 transition-colors">
                  <td className="pl-6 py-4">
                    <div className="flex flex-col">
                      <span className="text-sm font-medium text-slate-700">
                        {rowDate.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })}
                      </span>
                      <span className="text-[11px] text-slate-400 font-medium">
                        {rowDate.toLocaleDateString('en-GB', { weekday: 'short' }).toUpperCase()}
                      </span>
                    </div>
                  </td>
                  
                  <td className="px-4 py-4">
                    <div className="flex flex-col gap-1 max-w-md">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold text-slate-900 line-clamp-1">{row.project_name}</span>
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-500 border border-slate-200">
                          #{row.project_code}
                        </span>
                      </div>
                      <div className="flex items-start gap-2 group/comment">
                        <MessageSquare className="h-3.5 w-3.5 text-slate-300 mt-0.5 shrink-0" />
                        <span className="text-xs text-slate-500 line-clamp-2 leading-relaxed italic">
                          {row.comment || "No notes provided"}
                        </span>
                      </div>
                    </div>
                  </td>

                  <td className="px-4 py-4">
                    <div className="flex items-center gap-3">
                      <div className="h-8 w-8 rounded-full bg-gradient-to-tr from-slate-100 to-slate-200 border border-slate-200 flex items-center justify-center text-slate-500 text-xs font-bold">
                        {row.emp_name?.split(' ').map(n => n[0]).join('')}
                      </div>
                      <div className="flex flex-col">
                        <span className="text-sm font-medium text-slate-700">{row.emp_name}</span>
                        <span className="text-[11px] text-slate-400 flex items-center gap-1">
                          <Activity className="h-3 w-3" />
                          {phaseLabels[row.Phase] || "Analysis"}
                        </span>
                      </div>
                    </div>
                  </td>

                  <td className="px-4 py-4 text-center">
                    <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-semibold border ${getStatusColor(row.project_status)}`}>
                      {row.project_status}
                    </span>
                  </td>

                  <td className="px-4 py-4 text-right">
                    <div className="flex flex-col items-end">
                      <span className="text-sm font-bold text-slate-900">{parseFloat(row.hours).toFixed(2)}</span>
                      <span className="text-[10px] text-slate-400 font-bold uppercase tracking-tighter">Hours</span>
                    </div>
                  </td>

                  <td className="pr-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      {isEditable ? (
                        <>
                          <button 
                            onClick={() => handleAction('edit', row.id)}
                            className="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-all"
                            title="Edit"
                          >
                            <Edit3 className="h-4 w-4" />
                          </button>
                          <button 
                            onClick={() => handleAction('delete', row.id)}
                            className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-md transition-all"
                            title="Delete"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </>
                      ) : (
                        <div className="p-1.5 text-slate-300" title="Locked (Past Week)">
                          <Clock className="h-4 w-4 opacity-50" />
                        </div>
                      )}
                      <button 
                        onClick={() => handleAction('duplicate', row.id)}
                        className="p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-md transition-all"
                        title="Duplicate"
                      >
                        <Copy className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
        
        {filteredData.length === 0 && (
          <div className="py-20 flex flex-col items-center justify-center text-slate-400">
            <AlertCircle className="h-10 w-10 mb-4 stroke-1" />
            <p className="text-sm">No records match your filters</p>
          </div>
        )}
      </div>
      
      {/* Footer / Pagination Placeholder */}
      <div className="px-6 py-3 bg-slate-50/30 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500 font-medium">
        <div>Showing 1 - {filteredData.length} of {filteredData.length} entries</div>
        <div className="flex items-center gap-1">
          <button className="p-1 rounded-md hover:bg-white hover:shadow-sm border border-transparent hover:border-slate-200 transition-all disabled:opacity-30" disabled>
            <ChevronLeft className="h-4 w-4" />
          </button>
          <div className="h-6 w-6 flex items-center justify-center bg-white shadow-sm border border-slate-200 rounded text-blue-600 font-bold">1</div>
          <button className="p-1 rounded-md hover:bg-white hover:shadow-sm border border-transparent hover:border-slate-200 transition-all disabled:opacity-30" disabled>
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  )
}

function App() {
  const [componentData, setComponentData] = useState(null)

  useEffect(() => {
    const onRender = (event) => {
      const data = event.detail.args
      setComponentData(data)
    }

    Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRender)
    Streamlit.setComponentReady()
    
    return () => {
      Streamlit.events.removeEventListener(Streamlit.RENDER_EVENT, onRender)
    }
  }, [])

  if (!componentData) {
    return <div className="p-8 text-slate-400 animate-pulse font-medium text-sm">Initializing dashboard...</div>
  }

  const { data, start_of_week, end_of_week, is_read_only } = componentData

  return (
    <div className="p-4 bg-transparent min-h-screen font-sans">
      <TimesheetTable 
        data={data} 
        startOfWeek={start_of_week} 
        endOfWeek={end_of_week} 
        isReadOnly={is_read_only} 
      />
    </div>
  )
}

export default App
