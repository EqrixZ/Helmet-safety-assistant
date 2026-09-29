import { createContext, useContext } from 'react'

export type DataVersionValue = { version: number; invalidate: () => void }

export const DataVersionContext = createContext<DataVersionValue>({ version: 0, invalidate: () => {} })

/** Global "cache buster": bump after detection finishes so every useAsync refetches. */
export function useDataVersion(): DataVersionValue {
  return useContext(DataVersionContext)
}
