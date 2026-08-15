import { useEffect, useMemo, useState } from "react";

import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Tooltip,
  Polyline,
  useMap,
} from "react-leaflet";

import {
  Brain,
  MapPin,
  Navigation,
  Route,
  ShieldCheck,
  Sparkles,
  Clock3,
  AlertTriangle,
  CheckCircle2,
  LoaderCircle,
  ChevronDown,
  MapPinned,
} from "lucide-react";

const API_URL = "/api/v1/intelligence/resolve";

const DEMO_ADDRESS =
  "يعبد بعد دوار ياسين ثاني دخلة يمين امشي 100 متر قرب صيدلية الامل";


function MapAutoFit({ points }) {
  const map = useMap();

  useEffect(() => {
    if (!points || points.length < 2) return;

    map.fitBounds(points, {
      padding: [70, 70],
      maxZoom: 17,
    });
  }, [points, map]);

  return null;
}


function MetricCard({
  icon: Icon,
  title,
  value,
  subtitle,
}) {
  return (
    <div className="metric-card">
      <div className="metric-title">
        <Icon size={18} />
        <span>{title}</span>
      </div>

      <div className="metric-value">
        {value}
      </div>

      {subtitle && (
        <div className="metric-subtitle">
          {subtitle}
        </div>
      )}
    </div>
  );
}


function App() {
  const [address, setAddress] = useState(
    DEMO_ADDRESS
  );

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");


  const analyze = async () => {
    if (!address.trim()) return;

    setLoading(true);
    setError("");

    try {
      const response = await fetch(API_URL, {
        method: "POST",

        headers: {
          "Content-Type": "application/json",
        },

        body: JSON.stringify({
          address: address.trim(),
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail || "فشل تحليل العنوان"
        );
      }

      setResult(data);
    } catch (err) {
      setError(
        err.message || "تعذر الاتصال بالمحرك"
      );
    } finally {
      setLoading(false);
    }
  };


  const summary = result?.summary;
  const navigation = result?.navigation;

  const anchor = navigation?.anchor;

  const destination =
    navigation?.final_destination;

  const validationPoi =
    navigation
      ?.best_candidate
      ?.validations?.[0]
      ?.best_match;


  const center = useMemo(() => {
    if (
      destination?.latitude &&
      destination?.longitude
    ) {
      return [
        destination.latitude,
        destination.longitude,
      ];
    }

    if (
      anchor?.latitude &&
      anchor?.longitude
    ) {
      return [
        anchor.latitude,
        anchor.longitude,
      ];
    }

    return [32.44543, 35.1757835];
  }, [destination, anchor]);


  const linePoints = useMemo(() => {
    const points = [];

    if (
      anchor?.latitude &&
      anchor?.longitude
    ) {
      points.push([
        anchor.latitude,
        anchor.longitude,
      ]);
    }

    if (
      destination?.latitude &&
      destination?.longitude
    ) {
      points.push([
        destination.latitude,
        destination.longitude,
      ]);
    }

    return points;
  }, [anchor, destination]);


  const fitPoints = useMemo(() => {
    const points = [];

    if (
      anchor?.latitude &&
      anchor?.longitude
    ) {
      points.push([
        anchor.latitude,
        anchor.longitude,
      ]);
    }

    if (
      destination?.latitude &&
      destination?.longitude
    ) {
      points.push([
        destination.latitude,
        destination.longitude,
      ]);
    }

    if (
      validationPoi?.latitude &&
      validationPoi?.longitude
    ) {
      points.push([
        validationPoi.latitude,
        validationPoi.longitude,
      ]);
    }

    return points;
  }, [
    anchor,
    destination,
    validationPoi,
  ]);


  return (
    <div dir="rtl" className="app-shell">

      <header className="top-header">
        <div className="header-inner">

          <div className="brand">
            <div className="brand-icon">
              <Navigation size={25} />
            </div>

            <div>
              <h1>NEXERA</h1>

              <p>
                Palestinian Address Intelligence Engine
              </p>
            </div>
          </div>


          <div className="engine-status">
            <span className="status-dot" />

            Intelligence Engine Online
          </div>

        </div>
      </header>


      <main className="main-container">

        <section className="hero">

          <div className="hero-label">
            <Sparkles size={18} />
            Smart Address Intelligence
          </div>

          <h2>
            اكتب العنوان
            <span> زي ما بتحكيه.</span>

            <br />

            وخلي المحرك يفهم الباقي.
          </h2>

          <p>
            نفهم المعالم، الدخلات، الاتجاهات
            والمسافات، ونحوّل الوصف الفلسطيني
            إلى نقطة جغرافية قابلة للتوجيه.
          </p>

        </section>


        <div className="main-grid">

          <section className="panel input-panel">

            <div className="panel-title">
              <Brain size={21} />

              <div>
                <h3>تحليل العنوان</h3>

                <p>
                  اكتب وصف الموقع بالطريقة الطبيعية
                </p>
              </div>
            </div>


            <textarea
              value={address}

              onChange={(e) =>
                setAddress(e.target.value)
              }

              placeholder="مثال: يعبد بعد دوار ياسين ثاني دخلة يمين..."

              rows={6}

              className="address-input"
            />


            <div className="actions">

              <button
                onClick={analyze}
                disabled={loading}
                className="analyze-button"
              >
                {loading ? (
                  <>
                    <LoaderCircle
                      size={19}
                      className="spin"
                    />

                    جاري التحليل...
                  </>
                ) : (
                  <>
                    <Sparkles size={19} />

                    تحليل العنوان
                  </>
                )}
              </button>


              <button
                className="example-button"

                onClick={() =>
                  setAddress(DEMO_ADDRESS)
                }
              >
                مثال جاهز
              </button>

            </div>


            {error && (
              <div className="error-box">
                <AlertTriangle size={18} />

                {error}
              </div>
            )}


            <div className="analysis-steps">

              {[
                {
                  label: "فهم العنوان",
                  icon: Brain,
                },
                {
                  label: "تحديد نقطة الاهتمام",
                  icon: MapPin,
                },
                {
                  label: "تحليل شبكة الطرق",
                  icon: Route,
                },
                {
                  label: "التحقق المكاني",
                  icon: ShieldCheck,
                },
              ].map((item, index) => {

                const Icon = item.icon;

                return (
                  <div
                    className="step-item"
                    key={item.label}
                  >

                    <div className="step-info">

                      <div className="step-icon">
                        <Icon size={17} />
                      </div>

                      <span>
                        {item.label}
                      </span>

                    </div>


                    {result ? (
                      <CheckCircle2
                        size={18}
                        className="success-icon"
                      />
                    ) : loading ? (
                      <LoaderCircle
                        size={18}

                        className={
                          index === 0
                            ? "spin loading-icon"
                            : "loading-icon faded"
                        }
                      />
                    ) : (
                      <span className="inactive-dot" />
                    )}

                  </div>
                );
              })}

            </div>


            {summary?.simulation && (
              <div className="simulation-box">

                <AlertTriangle size={17} />

                <div>
                  <strong>
                    Simulation Mode
                  </strong>

                  <p>
                    بيانات الحواجز حاليًا محاكاة
                    حتى تفعيل Aween Rayeh Live API.
                  </p>
                </div>

              </div>
            )}

          </section>


          <section className="panel map-panel">

            <div className="map-header">

              <div className="panel-title">
                <MapPinned size={21} />

                <div>
                  <h3>
                    الخريطة الذكية
                  </h3>

                  <p>
                    المرجع، الوجهة ونقطة التحقق
                  </p>
                </div>
              </div>


              {summary?.final_confidence != null && (
                <div className="confidence-badge">

                  Confidence

                  <strong>
                    {Math.round(
                      summary.final_confidence * 100
                    )}
                    %
                  </strong>

                </div>
              )}

            </div>


            <div className="map-legend">

              <div>
                <span className="legend-dot anchor-dot" />
                المرجع
              </div>

              <div>
                <span className="legend-dot destination-dot" />
                الوجهة
              </div>

              <div>
                <span className="legend-dot validation-dot" />
                نقطة التحقق
              </div>

            </div>


            <div className="map-wrapper">

              <MapContainer
                key={center.join("-")}
                center={center}
                zoom={16}
                scrollWheelZoom
                zoomControl
              >

                <MapAutoFit
                  points={fitPoints}
                />


                <TileLayer
                  attribution={
                    '&copy; OpenStreetMap contributors &copy; CARTO'
                  }

                  url={
                    "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
                  }
                />


                {linePoints.length > 1 && (
                  <Polyline
                    positions={linePoints}

                    pathOptions={{
                      color: "#020617",
                      weight: 13,
                      opacity: 0.5,
                      lineCap: "round",
                      lineJoin: "round",
                    }}
                  />
                )}


                {linePoints.length > 1 && (
                  <Polyline
                    positions={linePoints}

                    pathOptions={{
                      color: "#06b6d4",
                      weight: 7,
                      opacity: 1,
                      lineCap: "round",
                      lineJoin: "round",
                    }}
                  />
                )}


                {anchor?.latitude &&
                  anchor?.longitude && (

                  <CircleMarker
                    center={[
                      anchor.latitude,
                      anchor.longitude,
                    ]}

                    radius={13}

                    pathOptions={{
                      color: "#ffffff",
                      weight: 4,
                      fillColor: "#06b6d4",
                      fillOpacity: 1,
                    }}
                  >

                    <Tooltip
                      permanent
                      direction="top"
                      offset={[0, -15]}
                      className="custom-map-tooltip"
                    >
                      المرجع: {anchor.name}
                    </Tooltip>

                  </CircleMarker>
                )}


                {destination?.latitude &&
                  destination?.longitude && (

                  <CircleMarker
                    center={[
                      destination.latitude,
                      destination.longitude,
                    ]}

                    radius={14}

                    pathOptions={{
                      color: "#ffffff",
                      weight: 4,
                      fillColor: "#22c55e",
                      fillOpacity: 1,
                    }}
                  >

                    <Tooltip
                      permanent
                      direction="bottom"
                      offset={[0, 16]}
                      className="custom-map-tooltip"
                    >
                      الوجهة المتوقعة
                    </Tooltip>

                  </CircleMarker>
                )}


                {validationPoi?.latitude &&
                  validationPoi?.longitude && (

                  <CircleMarker
                    center={[
                      validationPoi.latitude,
                      validationPoi.longitude,
                    ]}

                    radius={11}

                    pathOptions={{
                      color: "#ffffff",
                      weight: 3,
                      fillColor: "#f59e0b",
                      fillOpacity: 1,
                    }}
                  >

                    <Tooltip
                      direction="right"
                      className="custom-map-tooltip"
                    >
                      تحقق: {validationPoi.name_ar}
                    </Tooltip>

                  </CircleMarker>
                )}

              </MapContainer>


              {result && (
                <div className="map-floating-card">

                  <span>
                    الوجهة المتوقعة
                  </span>

                  <strong>
                    {navigation?.administrative_area}
                  </strong>

                  <small>
                    {destination?.latitude?.toFixed(6)}
                    ,{" "}
                    {destination?.longitude?.toFixed(6)}
                  </small>

                </div>
              )}

            </div>

          </section>

        </div>


        {result && (
          <>

            <section className="metrics-grid">

              <MetricCard
                icon={MapPin}
                title="الوجهة"

                value={
                  navigation?.administrative_area || "—"
                }

                subtitle={
                  destination
                    ? `${destination.latitude.toFixed(
                        6
                      )}, ${destination.longitude.toFixed(
                        6
                      )}`
                    : "—"
                }
              />


              <MetricCard
                icon={Brain}
                title="الثقة النهائية"

                value={`${Math.round(
                  (summary?.final_confidence || 0)
                  * 100
                )}%`}

                subtitle="Navigation + Spatial Validation"
              />


              <MetricCard
                icon={Clock3}
                title="المسافة المفسرة"

                value={`${summary?.interpreted_navigation_distance_m || 0} م`}

                subtitle="حسب التعليمات الوصفية"
              />


              <MetricCard
                icon={ShieldCheck}
                title="حالة الحاجز"

                value={
                  summary?.checkpoint_status ||
                  "غير معروف"
                }

                subtitle={
                  summary?.checkpoint || "—"
                }
              />

            </section>


            <section className="details-grid">

              <div className="panel details-panel">

                <div className="panel-title">
                  <Route size={21} />

                  <div>
                    <h3>
                      كيف فهمنا العنوان؟
                    </h3>

                    <p>
                      تفسير المحرك خطوة بخطوة
                    </p>
                  </div>
                </div>


                <div className="interpretation-card">

                  <span>
                    نقطة المرجع
                  </span>

                  <strong>
                    {anchor?.name}
                  </strong>

                  <small>
                    العلاقة: {anchor?.relation}
                  </small>

                </div>


                {navigation?.instructions?.map(
                  (instruction, index) => (

                  <div
                    key={index}
                    className="interpretation-card"
                  >

                    <span>
                      خطوة {index + 1}
                    </span>

                    <strong>
                      {instruction.raw_text}
                    </strong>

                    <small className="confidence-text">
                      ثقة الفهم:{" "}
                      {Math.round(
                        (instruction.confidence || 0)
                        * 100
                      )}
                      %
                    </small>

                  </div>

                ))}


                {navigation?.validation_landmarks?.map(
                  (landmark, index) => (

                  <div
                    key={index}
                    className="validation-card"
                  >

                    <span>
                      تحقق مكاني
                    </span>

                    <strong>
                      {landmark.text}
                    </strong>

                    <small>
                      العلاقة: {landmark.relation}
                    </small>

                  </div>

                ))}

              </div>


              <div className="panel details-panel">

                <div className="delivery-header">

                  <div className="panel-title">

                    <Navigation size={21} />

                    <div>
                      <h3>
                        قرار التوصيل
                      </h3>

                      <p>
                        أفضل خيار حسب التحليل الحالي
                      </p>
                    </div>

                  </div>


                  <span className="recommended-badge">
                    Recommended
                  </span>

                </div>


                <div className="route-result">

                  <span>
                    أفضل مسار
                  </span>

                  <h3>
                    {summary?.recommended_delivery_route || "—"}
                  </h3>


                  <div className="route-stats">

                    <div>
                      <span>
                        الحاجز
                      </span>

                      <strong>
                        {summary?.checkpoint || "—"}
                      </strong>
                    </div>


                    <div>
                      <span>
                        الحالة
                      </span>

                      <strong className="route-open">
                        {summary?.checkpoint_status || "—"}
                      </strong>
                    </div>

                  </div>

                </div>


                <div className="algorithms-box">

                  <span>
                    Pathfinding Engine
                  </span>


                  <div className="algorithm-tags">

                    {summary?.pathfinding_algorithms?.map(
                      algorithm => (

                      <div
                        key={algorithm}
                        className="algorithm-tag"
                      >
                        {algorithm}
                      </div>

                    ))}

                  </div>


                  {summary?.algorithms_same_distance && (

                    <div className="algorithm-success">

                      <CheckCircle2 size={16} />

                      الخوارزميات وصلت لنفس أقصر مسار

                    </div>

                  )}

                </div>

              </div>

            </section>


            <details className="technical-details">

              <summary>

                <div>
                  <strong>
                    التفاصيل التقنية
                  </strong>

                  <span>
                    Raw Engine Response
                  </span>
                </div>

                <ChevronDown size={20} />

              </summary>


              <pre dir="ltr">
                {JSON.stringify(
                  result,
                  null,
                  2
                )}
              </pre>

            </details>

          </>
        )}

      </main>

    </div>
  );
}


export default App;
