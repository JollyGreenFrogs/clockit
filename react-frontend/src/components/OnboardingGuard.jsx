import { useState, useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'
import Onboarding from '../components/Onboarding'
import Loading from '../components/Loading'

function OnboardingGuard({ children }) {
  const { isAuthenticated, checkOnboardingStatus } = useAuth()
  const [onboardingStatus, setOnboardingStatus] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const checkOnboarding = async () => {
      if (isAuthenticated) {
        const status = await checkOnboardingStatus()
        setOnboardingStatus(status)
      }
      setLoading(false)
    }

    checkOnboarding()
  }, [isAuthenticated, checkOnboardingStatus])

  // Show loading while checking onboarding status
  if (loading) {
    return <Loading />
  }

  // Show onboarding if user needs it
  if (isAuthenticated && onboardingStatus?.needs_onboarding) {
    return <Onboarding />
  }

  // Show main app if onboarding is complete or user is not authenticated
  return children
}

export default OnboardingGuard