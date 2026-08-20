"""
Profiling pipeline dengan cProfile.
Hasil disimpan ke dev_tools/profile_pipeline.prof
"""
import sys, os, cProfile, pstats, io, uuid, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dev_tools.benchmark_pipeline import generate_large_ccm
from fastra_core.knowledge.loader import create_fastra_knowledge_graph
from fastra_core.compiler.compiler_pipeline import QuantityCompilerPipeline

def main():
    random.seed(42)
    print("Memuat KG...")
    kg = create_fastra_knowledge_graph()
    print("Membangun CCM 10k...")
    ccm = generate_large_ccm(10000)
    pipeline = QuantityCompilerPipeline(kg, generated_at="2026-08-19T00:00:00+00:00")

    profiler = cProfile.Profile()
    profiler.enable()
    r = pipeline.compile(ccm, "JAKARTA")
    profiler.disable()

    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats(30)
    print(s.getvalue())
    profiler.dump_stats(os.path.join(os.path.dirname(__file__), "profile_pipeline.prof"))
    print("Profil disimpan.")

if __name__ == "__main__":
    main()