;; Compute the lattice-property metrics of conexp-clj (conexp.fca.metrics)
;; for the concept lattice of one formal context.
;;
;; Usage (classpath = `lein classpath` of conexp-clj):
;;     java -cp <classpath> clojure.main conexp_metrics.clj <context.cxt>
;;
;; Prints one `name<TAB>value` line per metric, flushed as soon as the metric
;; is computed, so a caller that kills this process on a timeout still gets
;; every metric finished so far. A metric that throws prints
;; `name<TAB>ERROR: <message>` and the remaining metrics are still computed.

(ns conexp-metrics
  (:require [conexp.io.contexts :refer [read-context]]
            [conexp.fca.contexts :refer [objects attributes reduce-context]]
            [conexp.fca.lattices :refer [concept-lattice lattice-base-set
                                         distributive? modular?]]
            [conexp.fca.metrics :as m]))

(defn- emit [name value]
  (println (str name "\t" value))
  (flush))

(defn- number-str [x]
  (if (ratio? x) (str (double x)) (str x)))

(defn- run-metric [name f]
  (try
    (emit name (number-str (f)))
    (catch Throwable e
      (emit name (str "ERROR: " (.getName (class e)) ": "
                      (some-> (.getMessage e) (.replaceAll "\\s+" " ")))))))

(let [[path] *command-line-args*
      ctx    (read-context path)
      lat    (concept-lattice ctx)]
  (emit "n_objects" (count (objects ctx)))
  (emit "n_attributes" (count (attributes ctx)))
  (emit "n_concepts" (count (lattice-base-set lat)))
  ;; cheapest first, so a timeout loses as little as possible
  (doseq [[name f] [["distributive"                        #(distributive? lat)]
                    ["modular"                             #(modular? lat)]
                    ["double_arrow_distributivity_index"   #(m/double-arrow-distributivity-index
                                                             (reduce-context ctx))]
                    ["birkhoff_distributivity_index"       #(m/birkhoff-distributivity-index ctx)]
                    ["distributivity_degree"               #(m/distributivity-degree lat)]
                    ["modularity_degree"                   #(m/modularity-degree lat)]
                    ["non_unit_meet_rise_rate"             #(m/non-unit-meet-rise-rate lat)]
                    ["non_unit_join_rise_rate"             #(m/non-unit-join-rise-rate lat)]
                    ["node_distributivity"                 #(m/node-distributivity lat)]
                    ["extent_weighted_node_distributivity" #(m/extent-weighted-node-distributivity lat)]]]
    (run-metric name f))
  (shutdown-agents))
