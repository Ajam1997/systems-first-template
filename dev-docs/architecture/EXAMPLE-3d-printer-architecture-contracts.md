# Desktop FDM 3D Printer — Architecture Contracts (EXAMPLE)

> **EXAMPLE FILE.** This is a worked example accompanying
> [architecture-contracts-format.md](architecture-contracts-format.md).
> It is **not** the real architecture for any project that ships with
> this template. Copy + adapt for your project.

**Owner:** @systems_lead
**Status:** living
**Last updated:** 2026-05-29
**Companion ICDs:** see `requirements/interfaces/IF-*.md`

## System overview

A desktop fused-deposition 3D printer for hobbyist/maker use. The
operator places a spool of filament, sends a sliced G-code file from
their laptop (USB or LAN), and the printer extrudes the file layer-
by-layer onto a heated bed without further intervention. Top-level
success criterion: print a 50 mm calibration cube within ±0.2 mm on
all axes, unattended, in under 90 minutes.

## Module table

| Module | Responsibilities | Inputs | Outputs | Owner | Performance envelope |
|---|---|---|---|---|---|
| **Main controller** | Interprets G-code, coordinates motion, hot end, bed; runs RTOS | G-code stream from host (`IF-1.1`); position FB from encoders (`IF-2.1`); thermistor readings (`IF-3.1`, `IF-3.2`) | Stepper step/dir pulses (`IF-2.2`); heater PWM (`IF-3.3`); fan PWM (`IF-3.4`); status to UI (`IF-4.1`) | firmware | NFR-1.1 motion command latency ≤2 ms |
| **Motion stage** | Mechanical X/Y/Z gantry: rails, belts, lead screws, frame | Step/dir pulses (`IF-2.2`); stepper power (rail map) | Toolhead position (mechanical); position FB to encoders (`IF-2.1`) | mechanical | KPM-2.1 positional accuracy ±0.1 mm; NFR-2.2 backlash ≤0.05 mm |
| **Stepper drivers** | 4-channel stepper driver board (X, Y, Z, E); micro-stepping; current limit | Step/dir pulses (`IF-2.2`); 24 V power | Coil currents to steppers (mechanical interface) | electrical | KPM-2.3 step jitter ≤1 µs; NFR-2.4 driver thermal margin ≥10 °C |
| **Hot end** | Heated nozzle assembly: heater cartridge, thermistor, heat-break, nozzle | Heater PWM (`IF-3.3`); 24 V power; filament from feeder | Molten filament onto bed; thermistor reading (`IF-3.1`) | mechanical+electrical (mechanical leads) | KPM-3.1 nozzle temp ±2 °C of setpoint at steady state |
| **Bed heater** | Heated build platform: silicone heater pad + thermistor + glass bed | Heater PWM (`IF-3.3`); 24 V power | Bed surface temperature; thermistor reading (`IF-3.2`) | mechanical+electrical (electrical leads) | KPM-3.2 bed-to-setpoint within 60 s; uniformity ±3 °C |
| **Filament feeder** | Extruder gear + stepper that pushes filament into hot end | Step/dir pulses for E axis (`IF-2.2`); 24 V; filament from spool | Filament flow to hot end | mechanical | NFR-5.1 slip-free up to 8 mm³/s flow |
| **Power supply** | 24 V / 5 V rails from AC mains | AC mains (90–250 V) | 24 V rail (steppers, heaters); 5 V rail (logic) | electrical | NFR-6.1 total system ≤300 W; KPM-6.1 24 V hold-up ≥10 ms |
| **Thermal safety monitor** | Hardware-priority cutoff for hot end + bed heaters if thermistor reads out-of-range or open | Thermistor readings (raw analog); heater PWM (passthrough) | HEATER_ENABLE (active-low, gates PWM) | electrical | KPM-7.1 fault-to-cutoff ≤2 s; NFR-7.2 not software-bypassable |
| **User interface** | LCD + rotary encoder; print start/stop, temperature, status | Status from main controller (`IF-4.1`); rotary encoder events | LCD frame, button events to main controller (`IF-4.2`) | firmware | NFR-4.1 UI frame ≥10 Hz |
| **Host interface** | USB or LAN bridge to operator's laptop | G-code file (USB MSC or HTTP upload) | G-code stream to main controller (`IF-1.1`); status to host (`IF-1.2`) | firmware+software (firmware leads on-device, software leads slicer integration) | NFR-1.3 upload ≥1 MB/s; NFR-1.4 USB compliance |

## Cross-cutting concerns

### Power rail map

| Rail | Source | Consumers | Budget |
|---|---|---|---|
| 24 V | Power supply | Stepper drivers, hot-end heater, bed heater | 250 W |
| 5 V (logic) | Power supply via buck | Main controller, UI, host interface, sensors | 5 W |
| 3.3 V (sensor) | Main controller LDO | Thermistors, encoders | 0.5 W |

Total budget 255.5 W of the 300 W NFR-6.1 envelope leaves 44.5 W
margin for transients (heater inrush, stepper acceleration).

### Thermal safety architecture (hardware-priority)

NFR-7.2 ("thermal safety must not be software-bypassable") drives
this. The **thermal safety monitor** is an electrical AND-gate
between the firmware's PWM output and the heater MOSFET gates:

```
PWM (firmware) ─┐
                 ├─AND→ heater MOSFET
HEATER_ENABLE ──┘   (active-high enables heater)
```

HEATER_ENABLE is asserted only when the safety monitor's
thermistor sense circuit reads in-range. Open or shorted
thermistor → HEATER_ENABLE de-asserts → MOSFET off regardless of
PWM state.

This explicitly violates the "one owner per module" rule because
the safety guarantee requires hardware enforcement on a path
firmware controls. The architecture contract clarifies that the
*gating logic* is the safety monitor's responsibility; the PWM
*generation* is the main controller's; both are documented
separately so neither lead assumes the other handles fault behavior.

### Compliance boundaries

- **EMC:** main controller's MCU clock + stepper switching are the
  emitters; bed heater PWM is the second-largest. EMC pre-compliance
  scope per IF crossings noted in IF-6.1.
- **Mains isolation:** power supply is the system's only mains-side
  module; everything else is SELV. Reinforced insulation per
  IEC 62368.
- **Laser:** N/A (this system has no laser).

## Cross-discipline boundaries (ICD seed list)

| From → To | IFs | Owners | Notes |
|---|---|---|---|
| Host interface → Main controller | IF-1.1, IF-1.2 | firmware ↔ firmware | Internal but documented for queue-depth contract |
| Main controller → Stepper drivers | IF-2.2 | firmware → electrical | Step/dir signal levels, max rate, isolation |
| Stepper drivers → Motion stage | (mechanical interface) | electrical → mechanical | Coil current, connector pinout (no IF — captured in BOM) |
| Encoders → Main controller | IF-2.1 | electrical → firmware | Position-FB encoding (quadrature vs serial) |
| Main controller → Hot end | IF-3.1, IF-3.3 | firmware → mechanical+electrical | Thermistor read; heater PWM |
| Main controller → Bed heater | IF-3.2, IF-3.3 | firmware → mechanical+electrical | Thermistor read; heater PWM |
| Thermal safety monitor → Heaters | IF-7.1 | electrical → electrical | HEATER_ENABLE gating signal |
| Main controller → UI | IF-4.1, IF-4.2 | firmware ↔ firmware | LCD display + button events |

## Open Questions if Frozen Mid-Authoring

- Stepper driver topology: discrete TMC2209 modules vs integrated
  STM32G4 + driver IC? Decision pending @electrical_lead's
  pre-compliance EMC pre-scan budget.
- Host interface: USB-only initially, or USB + Ethernet at first
  release? Decision pending @firmware_lead's RTOS stack assessment.
- Mechanical: Linear rails vs V-slot extrusion for X/Y? Affects
  NFR-2.2 backlash KPM. Decision pending @mechanical_lead's
  prototype build.
- Auto bed leveling: in scope or stretch? @systems_lead to decide
  before Stage 2 PDR.

---

## See also

- [architecture-contracts-format.md](architecture-contracts-format.md) — the spec this example follows
- `requirements/interfaces/IF-*.md` — the per-boundary ICDs that elaborate the cross-discipline rows
- `dev-docs/architecture/<feature>-engineer-brief.md` — per-feature briefs reference modules from this doc by name
