/**
 * Auth Store con Zustand per gestione stato autenticazione
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { authAPI } from './api'

export const useAuthStore = create(
  persist(
    (set, get) => ({
      // State
      isAuthenticated: false,
      user: null,
      loading: false,
      error: null,

      // Actions
      login: async (credentials) => {
        set({ loading: true, error: null })
        
        try {
          const response = await authAPI.login(credentials)
          set({
            isAuthenticated: true,
            user: response.user,
            loading: false,
            error: null
          })
          return response
        } catch (error) {
          set({
            isAuthenticated: false,
            user: null,
            loading: false,
            error: error.response?.data?.message || 'Errore di login'
          })
          throw error
        }
      },

      logout: async () => {
        set({ loading: true })
        
        try {
          await authAPI.logout()
        } catch (error) {
          console.error('Logout error:', error)
        } finally {
          set({
            isAuthenticated: false,
            user: null,
            loading: false,
            error: null
          })
        }
      },

      getCurrentUser: async () => {
        if (!get().isAuthenticated) return null
        
        try {
          const user = await authAPI.getCurrentUser()
          set({ user })
          return user
        } catch (error) {
          // Token probabilmente scaduto
          get().logout()
          return null
        }
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        isAuthenticated: state.isAuthenticated,
        user: state.user
      })
    }
  )
)