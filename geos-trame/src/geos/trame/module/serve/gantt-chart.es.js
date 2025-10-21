import { ref as x, computed as S, watch as C, onMounted as W, createElementBlock as G, openBlock as I, Fragment as X, createElementVNode as i, createCommentVNode as Y, normalizeStyle as O, toDisplayString as N, createTextVNode as _, withDirectives as $, vModelText as F, nextTick as q } from "vue";
import * as l from "d3";
const J = (y, h) => {
  const r = y.__vccOpts || y;
  for (const [g, f] of h)
    r[g] = f;
  return r;
}, K = { class: "text-sm font-semibold text-gray-700 mb-2" }, Q = { class: "text-xs font-medium text-gray-600" }, Z = { class: "text-xs font-medium text-gray-600" }, tt = { class: "text-xs font-medium text-gray-600" }, et = { class: "mt-3 flex justify-between items-center" }, nt = { class: "text-xs font-bold text-blue-600" }, at = {
  __name: "GanttChart",
  props: {
    tasks: Array,
    startDate: String,
    endDate: String
  },
  emits: ["task-hovered", "task-moved"],
  setup(y, { emit: h }) {
    const r = y, g = h, f = x(null), A = x(0), d = { top: 40, right: 20, bottom: 30, left: 50 }, B = S(() => r.tasks.length * 40 + d.top + d.bottom), D = x(!1), V = (t, e) => {
      if (!t || !e) return 0;
      const a = new Date(t), o = new Date(e);
      if (a.getTime() > o.getTime()) return 0;
      const b = Math.abs(o.getTime() - a.getTime());
      return Math.ceil(b / (1e3 * 60 * 60 * 24)) + 1;
    }, z = (t, e) => {
      if (!t || e <= 0) return t;
      const a = new Date(t);
      return a.setDate(a.getDate() + e - 1), l.timeFormat("%Y-%m-%d")(a);
    }, n = x(null), L = S(() => n.value ? V(n.value.start, n.value.end) : 0), M = S(() => {
      if (!n.value || !n.value.x || !n.value.y) return {};
      const t = d.left;
      return {
        position: "absolute",
        left: `${n.value.x + t}px`,
        top: `${n.value.y + d.top + 5}px`,
        // Place sous la barre
        transform: "translateX(-50%)",
        zIndex: 30,
        minWidth: "320px"
        // Agrandir le formulaire pour les 3 champs
      };
    }), P = (t, e) => {
      const a = c.value(new Date(t.start)), o = m.value(t.name);
      n.value = {
        id: t.id,
        name: t.name,
        start: t.start,
        end: t.end,
        // Initialiser la durée à partir des dates actuelles
        durationDays: V(t.start, t.end),
        x: a,
        y: o
      }, q(() => {
        document.querySelector(".gantt-edit-form input").focus();
      });
    };
    C(() => {
      var t;
      return (t = n.value) == null ? void 0 : t.durationDays;
    }, (t, e) => {
      n.value && t && t !== e && (n.value.end = z(n.value.start, t));
    }), C(() => {
      var t;
      return (t = n.value) == null ? void 0 : t.start;
    }, (t, e) => {
      n.value && t && t !== e && (n.value.end = z(t, n.value.durationDays));
    });
    const R = () => {
      const { id: t, name: e, start: a, end: o } = n.value, b = new Date(a), s = new Date(o);
      if (b.getTime() >= s.getTime()) {
        console.error("La date de début doit être strictement antérieure à la date de fin."), alert("La date de début doit être strictement antérieure à la date de fin.");
        return;
      }
      g("task-moved", {
        id: t,
        name: e,
        newStart: a,
        newEnd: o
      }), n.value = null;
    }, c = x(null), m = x(null), j = (t) => {
      const e = new Date(r.startDate), a = new Date(r.endDate);
      c.value = l.scaleTime().domain([e, a]).range([0, t - d.left - d.right]), m.value = l.scaleBand().domain(r.tasks.map((o) => o.name)).range([0, r.tasks.length * 40]).paddingInner(0.1);
    }, T = () => {
      if (!r.tasks.length || !f.value) return;
      A.value = f.value.clientWidth;
      const t = A.value;
      j(t);
      const e = l.select(f.value);
      e.selectAll("*").remove();
      const o = e.append("svg").attr("width", t).attr("height", B.value).append("g").attr("transform", `translate(${d.left}, ${d.top})`);
      o.append("g").attr("transform", `translate(0, ${r.tasks.length * 40})`).call(l.axisBottom(c.value)), o.append("g").call(l.axisLeft(m.value));
      const b = l.drag().on("start", function(s, u) {
        D.value = !1, l.select(this).raise().classed("dragging", !0), console.log(`DRAG START: Tentative de glisser la tâche: ${u.name}`);
      }).on("drag", function(s, u) {
        D.value = !0;
        const p = s.x;
        l.select(this).attr("x", p), console.log(`DRAG: Position X: ${p}`);
      }).on("end", function(s, u) {
        if (l.select(this).classed("dragging", !1), D.value) {
          const p = c.value.invert(s.x), k = new Date(u.end).getTime() - new Date(u.start).getTime(), E = new Date(p.getTime() + k), w = l.timeFormat("%Y-%m-%d")(p), v = l.timeFormat("%Y-%m-%d")(E);
          console.log(`DRAG END: Nouvelle date de début calculée: ${w}`), g("task-moved", {
            id: u.id,
            name: u.name,
            newStart: w,
            newEnd: v
          });
        }
        D.value = !1;
      });
      r.tasks.forEach((s) => {
        const u = c.value(new Date(s.start)), k = c.value(new Date(s.end)) - u, E = m.value(s.name), w = o.append("rect").datum(s).attr("x", u).attr("y", E).attr("width", k).attr("height", m.value.bandwidth()).attr("fill", s.color).attr("rx", 4).style("cursor", "grab").on("mouseenter", (v) => {
          const [H, U] = l.pointer(v);
          g("task-hovered", { task: s, isHovering: !0, x: H + d.left, y: U + d.top }), l.select(v.currentTarget).style("filter", "brightness(1.1)");
        }).on("mouseleave", (v) => {
          g("task-hovered", { task: s, isHovering: !1 }), l.select(v.currentTarget).style("filter", "none");
        }).on("dblclick", function(v) {
          P(s);
        });
        b(w);
      }), o.selectAll(".task-label").data(r.tasks).enter().append("text").text((s) => s.name).attr("x", (s) => c.value(new Date(s.start)) + 5).attr("y", (s) => m.value(s.name) + m.value.bandwidth() / 2 + 5).attr("fill", "black").style("pointer-events", "none").style("font-size", "12px");
    };
    return W(() => {
      window.addEventListener("resize", T), T();
    }), C(
      () => r.tasks,
      () => {
        T();
      },
      { deep: !0 }
    ), (t, e) => (I(), G(X, null, [
      i("div", {
        ref_key: "ganttContainer",
        ref: f,
        class: "relative w-full overflow-x-auto"
      }, null, 512),
      n.value ? (I(), G("div", {
        key: 0,
        style: O(M.value),
        class: "gantt-edit-form p-4 border border-blue-400 rounded-lg shadow-xl flex flex-col space-y-2 z-50"
      }, [
        i("div", K, "Éditer: " + N(n.value.name), 1),
        i("label", Q, [
          e[4] || (e[4] = _(" Durée (jours): ", -1)),
          $(i("input", {
            type: "number",
            "onUpdate:modelValue": e[0] || (e[0] = (a) => n.value.durationDays = a),
            min: "1",
            class: "mt-1 p-1 border rounded-md w-full text-sm focus:ring-blue-500 focus:border-blue-500"
          }, null, 512), [
            [
              F,
              n.value.durationDays,
              void 0,
              { number: !0 }
            ]
          ])
        ]),
        e[7] || (e[7] = i("hr", { class: "border-gray-200 my-1" }, null, -1)),
        i("label", Z, [
          e[5] || (e[5] = _(" Début: ", -1)),
          $(i("input", {
            type: "date",
            "onUpdate:modelValue": e[1] || (e[1] = (a) => n.value.start = a),
            class: "mt-1 p-1 border rounded-md w-full text-sm focus:ring-blue-500 focus:border-blue-500"
          }, null, 512), [
            [F, n.value.start]
          ])
        ]),
        i("label", tt, [
          e[6] || (e[6] = _(" Fin: ", -1)),
          $(i("input", {
            type: "date",
            "onUpdate:modelValue": e[2] || (e[2] = (a) => n.value.end = a),
            class: "mt-1 p-1 border rounded-md w-full text-sm focus:ring-blue-500 focus:border-blue-500"
          }, null, 512), [
            [F, n.value.end]
          ])
        ]),
        i("div", et, [
          i("span", nt, " Durée effective: " + N(L.value) + " j. ", 1),
          i("button", {
            onClick: R,
            class: "bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold py-1 px-3 rounded-md transition duration-150"
          }, " Valider ")
        ]),
        i("button", {
          onClick: e[3] || (e[3] = (a) => n.value = null),
          class: "absolute top-1 right-1 text-gray-500 hover:text-gray-800 text-xs"
        }, " × ")
      ], 4)) : Y("", !0)
    ], 64));
  }
}, lt = /* @__PURE__ */ J(at, [["__scopeId", "data-v-42cc02f8"]]);
export {
  lt as GanttChart
};
