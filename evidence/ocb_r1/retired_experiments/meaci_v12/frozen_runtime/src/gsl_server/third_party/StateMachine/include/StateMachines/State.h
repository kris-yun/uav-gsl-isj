#pragma once
namespace StateMachines
{
    // forward declaration for friend statement
    template <class T>
    class StateMachine;

    /*this class is templated so you can control the type of the arguments that are passed to the functions
    Almost always, the way it is supposed to be used is:

    class My_State : public State<My_State>
    {};

    ...

    class Whatever
    {
        StateMachine<My_State> sm;
        ...
    };

    That way, inside of (for example) CanExitState(next), you know that the next state is not just any State, but specifically My_State,
    and can access its members accordingly.
    */

    template <class T>
    class State
    {
        friend class StateMachine<T>;

    public:
        State() = default;
        State(const State<T>& other) = default;
        ~State() = default;

        virtual bool CanEnterState(const T* previousState) const
        {
            return true;
        }
        virtual bool CanExitState(const T* nextState) const
        {
            return true;
        }

    protected:
        virtual void OnEnterState(T* previousState) = 0;
        virtual void OnExitState(T* nextState) = 0;
    };
} // namespace StateMachines