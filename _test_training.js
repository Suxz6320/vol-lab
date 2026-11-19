
      lucide.createIcons();

      // ============ 状态 ============
      const STORAGE_KEY = "vl-training-records";
      const POS_NAMES = { outside: "主攻", setter: "二传", opposite: "接应", libero: "自由人", middle: "副攻" };
      const POS_ACTIONS = {
        outside: ["扣球", "吊球", "后排攻", "一传"],
        setter:  ["传球", "背传", "垫球"],
        opposite:["扣球", "拦网", "后排攻"],
        libero:  ["防守", "鱼跃救球", "一传"],
        middle:  ["快攻", "拦网", "时间差"],
      };

      // 示例数据（首次使用时写 localStorage）
      const SAMPLE = [
        { pos: "outside", action: "扣球", groups: "3 组 · 20 次", duration: "40 分钟", note: "发力链练习", date: new Date().toISOString().slice(0,10) },
        { pos: "libero",  action: "防守", groups: "4 组 · 30 次", duration: "50 分钟", note: "斜线与吊球预判", date: "2026-11-17" },
        { pos: "setter",  action: "传球", groups: "2 组 · 25 次", duration: "35 分钟", note: "背传节奏", date: "2026-11-17" },
        { pos: "opposite",action: "拦网", groups: "2 组 · 15 次", duration: "25 分钟", note: "双人配合时机", date: "2026-11-17" },
        { pos: "middle",  action: "快攻", groups: "3 组 · 18 次", duration: "30 分钟", note: "短平快节奏", date: "2026-11-17" },
      ];

      let records = loadRecords();
      let currentFilter = "all";

      function loadRecords() {
        try {
          const raw = localStorage.getItem(STORAGE_KEY);
          if (raw) return JSON.parse(raw);
        } catch(e) {}
        localStorage.setItem(STORAGE_KEY, JSON.stringify(SAMPLE));
        return SAMPLE.slice();
      }
      function saveRecords() {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(records));
      }

      // ============ 渲染 ============
      function renderList() {
        const list = document.getElementById("tr-record-list");
        const empty = document.getElementById("tr-empty");
        list.innerHTML = "";

        // 按日期分组
        const groups = {};
        records.filter(r => currentFilter === "all" || r.pos === currentFilter)
               .forEach(r => { (groups[r.date] = groups[r.date] || []).push(r); });

        const groupDates = Object.keys(groups).sort((a,b) => b.localeCompare(a));

        if (groupDates.length === 0) {
          empty.style.display = "flex";
          list.style.display = "none";
          return;
        }
        empty.style.display = "none";
        list.style.display = "";

        groupDates.forEach(date => {
          const head = document.createElement("div");
          head.className = "tr-group-head";
          head.textContent = formatDate(date);
          list.appendChild(head);

          groups[date].forEach(r => {
            const card = document.createElement("article");
            card.className = "tr-record-card pos-" + r.pos;
            card.innerHTML = `
              <div class="tr-record-row1">
                <div class="tr-record-title">${POS_NAMES[r.pos]} · ${r.action}</div>
                <div class="tr-record-stats">${r.groups}</div>
              </div>
              <div class="tr-record-row2">${r.duration}${r.note ? " · 备注：" + r.note : ""}</div>
            `;
            list.appendChild(card);
          });
        });

        updateStats();
      }

      function formatDate(d) {
        const today = new Date().toISOString().slice(0,10);
        if (d === today) return "今天";
        // 昨天
        const y = new Date(); y.setDate(y.getDate()-1);
        if (d === y.toISOString().slice(0,10)) return "昨天";
        return d.slice(5);  // MM-DD
      }

      function updateStats() {
        // 三个数字
        const total = records.length;
        const hrs = Math.round(records.reduce((s,r) => s + (parseInt(r.duration)||0), 0) / 60 * 10) / 10;
        const days = [...new Set(records.map(r => r.date))].sort((a,b) => b.localeCompare(a));
        let streak = 0;
        const today = new Date();
        for (let i=0; i<30; i++) {
          const d = new Date(today); d.setDate(d.getDate()-i);
          if (days.includes(d.toISOString().slice(0,10))) streak++; else break;
        }
        document.getElementById("tr-num-total").textContent = total;
        document.getElementById("tr-num-hrs").textContent = hrs;
        document.getElementById("tr-num-streak").textContent = streak;

        // 7 根柱状图（近 7 天，从最远 → 今天）
        renderWeeklyBars();
      }

      function renderWeeklyBars() {
        const container = document.getElementById("tr-bars");
        if (!container) return;
        container.innerHTML = "";

        // 近 7 天日期
        const dates = [];
        const today = new Date();
        for (let i=6; i>=0; i--) {
          const d = new Date(today); d.setDate(d.getDate()-i);
          dates.push(d.toISOString().slice(0,10));
        }
        const todayKey = dates[6];

        // 每天记录数
        const counts = dates.map(date => records.filter(r => r.date === date).length);
        const maxCount = Math.max(1, ...counts);  // 至少 1 避免除零

        counts.forEach((count, i) => {
          const bar = document.createElement("div");
          const isToday = dates[i] === todayKey;
          const hasData = count > 0;

          if (!hasData) {
            bar.className = "tr-bar empty";
            bar.style.height = "2px";
          } else {
            bar.className = "tr-bar" + (isToday ? " today" : "");
            // 高度：2 ~ 40px 之间，按比例
            const h = Math.max(4, Math.round((count / maxCount) * 38 + 2));
            bar.style.height = h + "px";
          }
          container.appendChild(bar);
        });
      }

      // ============ 筛选交互 ============
      const chips = document.querySelectorAll(".tr-filter-chip");
      chips.forEach(chip => {
        chip.addEventListener("click", () => {
          chips.forEach(c => c.classList.remove("active"));
          chip.classList.add("active");
          currentFilter = chip.dataset.pos;
          renderList();
        });
      });

      // URL 参数自动过滤：training.html?pos=outside
      const urlParams = new URLSearchParams(location.search);
      const initPos = urlParams.get("pos");
      if (initPos && [...chips].some(c => c.dataset.pos === initPos)) {
        currentFilter = initPos;
        const target = [...chips].find(c => c.dataset.pos === initPos);
        if (target) {
          chips.forEach(c => c.classList.remove("active"));
          target.classList.add("active");
        }
      }

      // ============ +记一次：简易表单弹窗 ============
      function openAddForm() {
        const overlay = document.createElement("div");
        overlay.style.cssText = "position:fixed;inset:0;background:rgba(0,0,0,0.65);z-index:100;display:flex;align-items:flex-end;justify-content:center;";
        overlay.innerHTML = `
          <div style="background:#1A212B;border:1px solid #2A3441;border-radius:20px 20px 0 0;width:100%;max-width:560px;padding:20px;box-sizing:border-box;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
              <div style="font-size:17px;font-weight:700;color:#EDF1F5;">记一次训练</div>
              <button id="form-close" style="background:none;border:none;color:#8C98A8;font-size:18px;">✕</button>
            </div>
            <label style="font-size:12px;color:#8C98A8;display:block;margin-bottom:4px;">位置</label>
            <select id="f-pos" style="width:100%;background:#171D26;border:1px solid #2A3441;color:#EDF1F5;padding:10px 12px;border-radius:8px;font-size:14px;margin-bottom:12px;">
              ${Object.entries(POS_NAMES).map(([k,v]) => `<option value="${k}">${v}</option>`).join("")}
            </select>
            <label style="font-size:12px;color:#8C98A8;display:block;margin-bottom:4px;">项目</label>
            <select id="f-action" style="width:100%;background:#171D26;border:1px solid #2A3441;color:#EDF1F5;padding:10px 12px;border-radius:8px;font-size:14px;margin-bottom:12px;">
              ${POS_ACTIONS.outside.map(a => `<option value="${a}">${a}</option>`).join("")}
            </select>
            <div style="display:flex;gap:10px;margin-bottom:12px;">
              <div style="flex:1;">
                <label style="font-size:12px;color:#8C98A8;display:block;margin-bottom:4px;">组数</label>
                <input id="f-groups" type="text" placeholder="3 组 · 20 次" value="3 组 · 20 次" style="width:100%;background:#171D26;border:1px solid #2A3441;color:#EDF1F5;padding:10px 12px;border-radius:8px;font-size:14px;box-sizing:border-box;">
              </div>
              <div style="flex:1;">
                <label style="font-size:12px;color:#8C98A8;display:block;margin-bottom:4px;">时长(分)</label>
                <input id="f-duration" type="number" value="30" style="width:100%;background:#171D26;border:1px solid #2A3441;color:#EDF1F5;padding:10px 12px;border-radius:8px;font-size:14px;box-sizing:border-box;">
              </div>
            </div>
            <label style="font-size:12px;color:#8C98A8;display:block;margin-bottom:4px;">备注（选填）</label>
            <input id="f-note" type="text" placeholder="例如：发力链练习" style="width:100%;background:#171D26;border:1px solid #2A3441;color:#EDF1F5;padding:10px 12px;border-radius:8px;font-size:14px;box-sizing:border-box;margin-bottom:16px;">
            <button id="f-save" style="width:100%;background:#F2A03C;color:#10151B;border:none;padding:13px;border-radius:999px;font-size:15px;font-weight:700;">保存训练</button>
          </div>
        `;
        document.body.appendChild(overlay);

        // 如果 URL 有 pos 参数，预选
        const posSel = overlay.querySelector("#f-pos");
        if (currentFilter !== "all") posSel.value = currentFilter;
        posSel.addEventListener("change", () => {
          const aSel = overlay.querySelector("#f-action");
          aSel.innerHTML = POS_ACTIONS[posSel.value].map(a => `<option value="${a}">${a}</option>`).join("");
        });

        const close = () => overlay.remove();
        overlay.querySelector("#form-close").addEventListener("click", close);
        overlay.addEventListener("click", e => { if (e.target === overlay) close(); });

        overlay.querySelector("#f-save").addEventListener("click", () => {
          records.unshift({
            pos: posSel.value,
            action: overlay.querySelector("#f-action").value,
            groups: overlay.querySelector("#f-groups").value || "-",
            duration: (overlay.querySelector("#f-duration").value || 30) + " 分钟",
            note: overlay.querySelector("#f-note").value,
            date: new Date().toISOString().slice(0,10),
          });
          saveRecords();
          renderList();
          close();
        });
      }

      document.querySelector(".tr-add-btn").addEventListener("click", openAddForm);
      document.querySelector(".tr-empty-btn").addEventListener("click", openAddForm);

      // 初始渲染
      renderList();
    
