export function Header() {
  return (
    <header className="border-b border-gray-200 bg-white">
      <div className="mx-auto max-w-3xl px-4 py-4 sm:px-6">
        <h1 className="text-2xl font-medium text-gray-900">
          IMDB Movies Analysis
        </h1>
        <p className="mt-1 text-sm text-gray-500">
          Explore the top-movies-per-year dataset with AI assistance
        </p>
      </div>
    </header>
  );
}
