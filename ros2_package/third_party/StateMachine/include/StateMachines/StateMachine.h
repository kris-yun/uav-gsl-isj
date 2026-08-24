#pragma once
#include <StateMachines/State.h>
#include <type_traits>

namespace StateMachines
{
    template <class T>
    class StateMachine
    {
    public:
        StateMachine()
        {
            static_assert(std::is_base_of<State<T>, T>::value, "Invalid template argument on StateMachine<T> class. T must be a class inheriting from StateMachine::State<T>\n");
            currentState = nullptr;
        }

        // sets currentState = next if both current->CanExitState() and next->CanEnterState() return true. If current == next, nothing happens
        void trySetState(T* next)
        {
            if (canChange(next))
                forceSetState(next);
        }
        // same as trySetState, but OnExitState and OnEnterState will trigger even if current == next
        void tryResetState(T* next)
        {
            if (canChange(next))
                forceResetState(next);
        }
        // same as trySetState, but does not check canEnter or canExit
        void forceSetState(T* next)
        {
            if (currentState != next)
                forceResetState(next);
        }
        // same as tryResetState, but does not check canEnter or canExit
        void forceResetState(T* next)
        {
            if (currentState != nullptr)
                AsBase(currentState)->OnExitState(next);
            T* previous = currentState;
            currentState = next;
            AsBase(currentState)->OnEnterState(previous);
        }
        T* getCurrentState() const
        {
            return currentState;
        }

    private:
        T* currentState;
        bool canChange(const T* next)
        {
            bool canDo = true;
            if (currentState != nullptr)
                canDo = canDo && currentState->CanExitState(next);

            if (next != nullptr)
                canDo = canDo && next->CanEnterState(currentState);
            else
                canDo = false;

            return canDo;
        }

        // required for the friend declaration to take effect, so this class can call OnEnter and OnExit
        State<T>* AsBase(T* ptr)
        {
            return dynamic_cast<State<T>*>(ptr);
        }
    };

} // namespace StateMachines