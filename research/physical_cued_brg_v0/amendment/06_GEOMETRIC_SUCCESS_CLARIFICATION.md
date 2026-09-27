# User-authorized geometric endpoint clarification

Received before closed-loop scoring on 2026-09-27.

Primary geometric success is the last finite valid source estimate available
within the 300 s search budget, with Euclidean truth error <= 0.5 m.
Timeout does not by itself change this geometric result. Report timeout and
algorithm declaration independently. A declared success with error > 0.5 m is
a wrong declaration. Service/TCP/navigation failure, absent finite estimate,
or nonfinite state is a geometric failure. Robot proximity to truth is auxiliary
and must never replace source-estimate success.

Required output columns: geometric_success, final_source_error_m,
algorithm_declared_success, timeout, wrong_declaration, declaration_time_s,
first_navigation_within_0.5m_time_s.

All four arms share this definition; House03 remains OPEN DEVELOPMENT.
