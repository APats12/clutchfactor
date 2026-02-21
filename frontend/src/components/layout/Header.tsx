import { Link } from 'react-router-dom'

export function Header() {
  return (
    <header className="border-b border-gray-200 bg-white">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4">
        <Link to="/" className="flex items-center gap-2">
          <span className="text-xl font-black tracking-tight text-gray-900">
            Clutch<span className="text-blue-600">Factor</span>
          </span>
          <span className="rounded bg-blue-600 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-widest text-white">
            Beta
          </span>
        </Link>
        <nav className="text-sm text-gray-500">
          NFL Win Probability &amp; SHAP Explainability
        </nav>
      </div>
    </header>
  )
}
