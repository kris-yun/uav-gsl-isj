#include <StateMachine.h>
#include <stdio.h>
#include <iostream>

using namespace StateMachines;

class My_State : public State<My_State>
{
    public:
    virtual int priority() const = 0;

    bool CanEnterState(const My_State* previousState) const override
    {
        return previousState->priority()<=priority();
    }
};

class StateA : public My_State
{
    int priority() const override
    {
        return 1;
    } 

    void OnEnterState(My_State* previous) override
    {
        printf("Entering State A\n");
    }

    void OnExitState(My_State* next) override
    {
        printf("Exiting State A\n");
    }

    void OnUpdate() override
    {
        printf("I'm on state A!\n");
    }
};

class StateB : public My_State
{
    int priority() const override
    {
        return 2;
    }

    void OnEnterState(My_State* previous) override
    {
        printf("Entering State B\n");
    }

    void OnExitState(My_State* next) override
    {
        printf("Exiting State B\n");
    }

    void OnUpdate() override
    {
        printf("I'm on state B!\n");
    }
};

class TestClass
{
    public:
    StateMachines::StateMachine<My_State> stateMachine;
    StateA stateA;
    StateB stateB;
};

int main()
{
    TestClass test;
    
    test.stateMachine.forceSetState(&test.stateA);


    char input = 'a';
    while(input != 'x')
    {
        std::cin >> input;
        if(input=='b')
            test.stateMachine.trySetState(&test.stateB);
        else if(input=='a')
            test.stateMachine.trySetState(&test.stateA);
        else if (input=='A')
        {
            test.stateMachine.forceResetState(&test.stateA);
        }
        test.stateMachine.getCurrentState()->OnUpdate();
    }
    
}