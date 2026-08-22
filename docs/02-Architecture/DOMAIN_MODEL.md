| Concept          | Type                    | السبب                             |
| ---------------- | ----------------------- | --------------------------------- |
| Workflow         | Entity + Aggregate Root | لأنه يملك الهوية ويحتوي الـ Steps |
| Step             | Entity                  | جزء من Workflow وله سلوك          |
| Execution        | Entity                  | يمثل تشغيلًا حقيقيًا              |
| Asset            | Entity                  | يمثل موردًا داخل النظام           |
| Trigger          | Entity                  | يدير بداية التنفيذ                |
| Duration         | Value Object            | قيمته هي هويته                    |
| Resolution       | Value Object            | لا يحتاج هوية مستقلة              |
| ExecutionService | Domain Service          | ينسق تنفيذ الـ Workflow           |
