from pipen import Proc, Pipen


class Process(Proc):
    input = 'a'
    output = 'b:file:b.txt'
    input_data = range(10)
    script = 'echo {{in.a}} > {{out.b}}'


pipeline = Pipen(
    outdir="/tmp/single_outdir_workdir_outdir",
    workdir="/tmp/single_outdir_workdir_workdir",
).set_start(Process)

if __name__ == '__main__':
    pipeline.run()
